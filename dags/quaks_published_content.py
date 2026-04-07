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
    "quaks_published_content",
    default_args=default_args,
    schedule="0 */6 * * *",
    catchup=False,
)


@task.kubernetes(
    image="bsantanna/java-python-dev",
    namespace="airflow",
    secrets=[Secret('env', None, 'quaks-dags-secrets')],
)
def process_published_content():
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

    # Fetch unprocessed records from ES
    search_resp = requests.post(
        f"{es_url}/quaks_published-content_latest/_search/template",
        headers=es_headers,
        json={
            "id": "get_published_content_unprocessed_template",
            "params": {"size": 100},
        },
    )
    search_resp.raise_for_status()
    hits = search_resp.json()["hits"]["hits"]
    print(f"Found {len(hits)} unprocessed published content records")

    # Skill name to destination index and document builder
    def build_news_analyst_doc(src):
        return {
            "date_reference": src["date_timestamp"][:10],
            "text_executive_summary": src["text_executive_summary"],
            "text_report_html": src["text_report_html"],
        }

    skill_routing = {
        "/news_analyst": {
            "index": "quaks_insights-news_latest",
            "build_doc": build_news_analyst_doc,
        },
    }

    def mark_processed(doc_index, doc_id):
        update_resp = requests.post(
            f"{es_url}/{doc_index}/_update/{doc_id}",
            headers=es_headers,
            json={"doc": {"flag_processed": True}},
        )
        update_resp.raise_for_status()
        print(f"Marked {doc_id} as processed")

    for hit in hits:
        doc_id = hit["_id"]
        doc_index = hit["_index"]
        src = hit["_source"]
        author_username = src["key_author_username"]
        skill_name = src["key_skill_name"]

        try:
            # Validate author exists and is active in Keycloak
            check_resp = requests.get(
                f"{kc_url}/admin/realms/{kc_realm}/users",
                headers=kc_headers,
                params={"username": author_username, "exact": "true"},
            )
            check_resp.raise_for_status()
            users = check_resp.json()

            if not users:
                print(f"Author not found in Keycloak: {author_username}, rejecting {doc_id}")
                mark_processed(doc_index, doc_id)
                continue

            if not users[0].get("enabled", False):
                print(f"Author account is disabled: {author_username}, rejecting {doc_id}")
                mark_processed(doc_index, doc_id)
                continue

            # Route to destination index based on skill name
            route = skill_routing.get(skill_name)
            if route is None:
                print(f"Unknown skill name: {skill_name}, rejecting {doc_id}")
                mark_processed(doc_index, doc_id)
                continue

            dest_doc = route["build_doc"](src)

            # Index into destination
            index_resp = requests.post(
                f"{es_url}/{route['index']}/_doc",
                headers=es_headers,
                json=dest_doc,
            )
            index_resp.raise_for_status()
            print(f"Routed {doc_id} to {route['index']}")

            mark_processed(doc_index, doc_id)

        except Exception as e:
            print(f"Error processing {doc_id} (author: {author_username}): {e}")


with dag:
    process_published_content()
