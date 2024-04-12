/**
 * Copyright 2024 Google LLC
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

locals {
  project_id = var.project_id
}

provider "google" {
  project = local.project_id
  region  = "us-central1"
  zone    = "us-central1-a"
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "= 3.46.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 3.46.0"
    }
  }
}

resource "google_project_service" "osconfig" {
  project = local.project_id
  service = "osconfig.googleapis.com"
}



output "project_nr" {
  value = var.project_nr
}

output "org_id" {
  value = var.org_id
}
output "folder_id" {
  value = var.folder_id
}

output "project_id" {
  value = local.project_id
}
output "instance_name" {
  value = var.instance_name
}
