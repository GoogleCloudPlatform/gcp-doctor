# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as: python3
"""Stub API calls used in gcf.py for testing.

Instead of doing real API calls, we return test JSON data.
"""

import json
import re

from gcpdiag.queries import apis_stub

#pylint: disable=unused-argument


class CloudBuildApiStub:
  """Mock object to simulate function api calls."""

  def projects(self):
    return self

  def locations(self):
    return self

  def builds(self):
    return CloudBuildBuildsApiStub()

  def triggers(self):
    return CloudBuildTriggersApiStub()


class CloudBuildBuildsApiStub:
  """Mock object to simulate functions of builds api calls."""

  def list(self, parent):
    m = re.match(r'projects/([^/]+)/', parent)
    project_id = m.group(1)
    return RestCallStub(project_id, 'cloudbuild.json')


class CloudBuildTriggersApiStub:
  """Mock object to simulate functions of triggers api calls."""

  def list(self, parent):
    m = re.match(r'projects/([^/]+)/', parent)
    project_id = m.group(1)
    return RestCallStub(project_id, 'cloudbuild-triggers.json')


class RestCallStub:
  """Mock object to simulate executable api request."""

  def __init__(self, project_id: str, json_file: str):
    self.json_dir = apis_stub.get_json_dir(project_id)
    self.json_file = json_file

  def execute(self, num_retries: int = 0) -> dict:
    with open(self.json_dir / self.json_file, encoding='utf-8') as json_file:
      return json.load(json_file)
