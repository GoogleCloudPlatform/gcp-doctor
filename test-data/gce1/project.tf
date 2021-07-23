/**
 * Copyright 2021 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

terraform {
  backend "gcs" {
    bucket = "gcpd-tf-state"
    prefix = "projects/gce"
  }
}

resource "google_project" "project" {
  name = "gcp-doctor test - gce1"
  # note: we add a "random" 2-byte suffix to make it easy to recreate the
  # project under another name and avoid project name conflicts.
  project_id      = "gcpd-gce1-4exv"
  org_id          = "98915863894"
  billing_account = "0072A3-8FBEBA-7CD837"
  skip_delete     = true
}

resource "google_project_service" "compute" {
  project = google_project.project.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  project = google_project.project.project_id
  service = "container.googleapis.com"
}

resource "google_compute_project_metadata_item" "serial_logging" {
  project = google_project.project.project_id
  key     = "serial-port-logging-enable"
  value   = "true"
}

data "google_compute_default_service_account" "default" {
  project = google_project.project.project_id
}

data "google_compute_image" "cos" {
  family  = "cos-85-lts"
  project = "cos-cloud"
}


output "project_id" {
  value = google_project.project.project_id
}
