terraform {
  backend "gcs" {
    bucket = "gcpd-apigee-1-lus4-tfstate"
  }
}

resource "google_project" "project" {
  name            = "gcpd-apigee-1-lus4"
  project_id      = "gcpd-apigee-1-lus4"
  org_id          = "126083999674"
  billing_account = "003745-B32D41-4F1D6A"
  skip_delete     = true
}

resource "google_project_service" "apigee" {
  project = google_project.project.project_id
  service = "apigee.googleapis.com"
}

resource "google_project_service" "compute" {
  project = google_project.project.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "servicenetworking" {
  project = google_project.project.project_id
  service = "servicenetworking.googleapis.com"
}

resource "google_project_service" "kms" {
  project = google_project.project.project_id
  service = "cloudkms.googleapis.com"
}

output "project_id" {
  value = google_project.project.project_id
}
