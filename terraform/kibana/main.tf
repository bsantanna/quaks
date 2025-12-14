terraform {
  required_providers {
    elasticstack = {
      source  = "elastic/elasticstack"
      version = "~> 0.12"
    }
  }
}

provider "elasticstack" {
  elasticsearch {
    endpoints = [var.es_url]
    api_key   = var.es_api_key
  }

  kibana {
    endpoints = [var.kb_url]
    api_key   = var.es_api_key
  }
}

resource "elasticstack_elasticsearch_security_role" "anonymous_dashboard_role" {
  name = "anonymous_dashboard_role"

  indices {
    names      = ["*"]
    privileges = ["read", "view_index_metadata"]
  }

  applications {
    application = "kibana-.kibana"
    privileges  = ["feature_dashboard.read"]
    resources   = ["*"]
  }

}

resource "elasticstack_elasticsearch_security_user" "anonymous_user" {
  username = var.kb_anonymous_username
  password_wo = var.kb_anonymous_password
  roles    = [elasticstack_elasticsearch_security_role.anonymous_dashboard_role.name]

  depends_on = [elasticstack_elasticsearch_security_role.anonymous_dashboard_role]
}

data "local_file" "stocks_eod_data_view_ndjson" {
  filename = "${path.module}/stocks_eod_data_view.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "data_view" {
  file_contents = data.local_file.stocks_eod_data_view_ndjson.content
  space_id  = "default"
  overwrite = true
}

data "local_file" "stocks_eod_visualizations_ndjson" {
  filename = "${path.module}/stocks_eod_visualizations.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "visualizations" {
  file_contents = data.local_file.stocks_eod_visualizations_ndjson.content
  space_id  = "default"
  overwrite = true
  depends_on = [elasticstack_kibana_import_saved_objects.data_view]
}

data "local_file" "stocks_eod_dashboard_ndjson" {
  filename = "${path.module}/stocks_eod_dashboard.ndjson"
}

resource "elasticstack_kibana_import_saved_objects" "dashboard" {
  file_contents = data.local_file.stocks_eod_dashboard_ndjson.content
  space_id  = "default"
  overwrite = true
  depends_on = [elasticstack_kibana_import_saved_objects.visualizations]
}
