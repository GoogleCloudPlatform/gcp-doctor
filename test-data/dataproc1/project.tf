resource "google_project" "project" {
  name            = "gcpdiag dataproc"
  project_id      = "gcpdiag-${random_string.project_id.id}"
  org_id          = var.org_id
  billing_account = var.billing_account_id
}

resource "google_project_service" "dataproc" {
  project            = google_project.project.project_id
  service            = "dataproc.googleapis.com"
  disable_on_destroy = false
}

resource "random_string" "project_id" {
  length  = 16
  number  = true
  lower   = true
  upper   = false
  special = false
}

output "project_id" {
  value = google_project.project.project_id
}
