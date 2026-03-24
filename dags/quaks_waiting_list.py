from airflow.sdk import DAG, task
from airflow.providers.cncf.kubernetes.secret import Secret
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "quaks_waiting_list",
    default_args=default_args,
    schedule="0 6 * * *",
    catchup=False,
)


@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def process_waiting_list():
    import os
    import requests

    es_url = os.environ["ELASTICSEARCH_URL"]
    es_api_key = os.environ["ELASTICSEARCH_API_KEY"]
    kc_url = os.environ["KEYCLOAK_ADMIN_URL"]
    kc_username = os.environ["KEYCLOAK_ADMIN_USERNAME"]
    kc_password = os.environ["KEYCLOAK_ADMIN_PASSWORD"]
    kc_realm = os.environ.get("KEYCLOAK_REALM", "quaks")

    es_headers = {
        "Authorization": f"ApiKey {es_api_key}",
        "Content-Type": "application/json",
    }

    # Obtain Keycloak admin token
    token_resp = requests.post(
        f"{kc_url}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": kc_username,
            "password": kc_password,
            "grant_type": "password",
        },
    )
    token_resp.raise_for_status()
    kc_token = token_resp.json()["access_token"]
    kc_headers = {
        "Authorization": f"Bearer {kc_token}",
        "Content-Type": "application/json",
    }

    # Fetch unprocessed records from ES using search template
    search_resp = requests.post(
        f"{es_url}/quaks_waiting-list_latest/_search/template",
        headers=es_headers,
        json={
            "id": "get_waiting_list_unprocessed_template",
            "params": {"size": 100},
        },
    )
    search_resp.raise_for_status()
    hits = search_resp.json()["hits"]["hits"]
    print(f"Found {len(hits)} unprocessed waiting list records")

    for hit in hits:
        doc_id = hit["_id"]
        doc_index = hit["_index"]
        src = hit["_source"]
        email = src["key_email"]
        username = src["key_username"]
        first_name = src["text_first_name"]
        last_name = src["text_last_name"]

        try:
            # Check if user already exists in Keycloak by email
            check_resp = requests.get(
                f"{kc_url}/admin/realms/{kc_realm}/users",
                headers=kc_headers,
                params={"email": email, "exact": "true"},
            )
            check_resp.raise_for_status()
            existing = check_resp.json()

            if not existing:
                # Create user with required password reset on first login
                create_resp = requests.post(
                    f"{kc_url}/admin/realms/{kc_realm}/users",
                    headers=kc_headers,
                    json={
                        "username": username,
                        "email": email,
                        "firstName": first_name,
                        "lastName": last_name,
                        "enabled": True,
                        "requiredActions": ["UPDATE_PASSWORD"],
                    },
                )
                if create_resp.status_code == 201:
                    # Extract user ID and send password reset email
                    user_id = create_resp.headers["Location"].rsplit("/", 1)[-1]
                    email_resp = requests.put(
                        f"{kc_url}/admin/realms/{kc_realm}/users/{user_id}/execute-actions-email",
                        headers=kc_headers,
                        json=["UPDATE_PASSWORD"],
                    )
                    if email_resp.status_code == 204:
                        print(f"Created Keycloak user and sent password email: {email}")
                    else:
                        print(f"Created user {email} but failed to send email: {email_resp.status_code}")
                elif create_resp.status_code == 409:
                    error_msg = create_resp.text
                    if "username" in error_msg.lower():
                        print(f"Username conflict for {email} (username: {username}), skipping - needs manual review")
                        continue
                    else:
                        print(f"User already exists (email conflict): {email}")
                else:
                    print(f"Failed to create user {email}: {create_resp.status_code} {create_resp.text}")
                    continue
            else:
                print(f"User already exists: {email}")

            # Mark record as processed
            update_resp = requests.post(
                f"{es_url}/{doc_index}/_update/{doc_id}",
                headers=es_headers,
                json={"doc": {"flag_processed": True}},
            )
            update_resp.raise_for_status()
            print(f"Marked {doc_id} as processed")

        except Exception as e:
            print(f"Error processing {email}: {e}")


with dag:
    process_waiting_list()
