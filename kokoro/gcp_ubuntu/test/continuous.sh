#!/bin/bash
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


set -e
set -x

PATH="${KOKORO_ARTIFACTS_DIR}/git/gcpdiag/bin:$HOME/.local/bin:$PATH"
cd "${KOKORO_ARTIFACTS_DIR}/git/gcpdiag"

# Test with Python 3.7
pipenv-dockerized 3.7 run pipenv install --dev
pipenv-dockerized 3.7 run make test
# remove previously installed packages and install only default packages
rm -rf .pipenv-dockerized/venv-3.7
pipenv-dockerized 3.7 run pipenv install --ignore-pipfile
# run gcpdiag-mocked
pipenv-dockerized 3.7 run make test-mocked

# Test with Python 3.9
pipenv-dockerized 3.9 run pipenv install --dev
pipenv-dockerized 3.9 run make test
# Note: we don't re-install without dev packages same as above,
#       because "make kokoro-build" needs dev packages.
pipenv-dockerized 3.9 run make test-mocked
# Build pyinstaller binary
pipenv-dockerized 3.9 run make -C kokoro kokoro-build

# Push docker images
gcloud -q components update
gcloud -q auth configure-docker us-docker.pkg.dev
make -C docker/gcpdiag build
make -C docker/gcpdiag push
make -C gcpdiag_google_internal/docker build
make -C gcpdiag_google_internal/docker push

# Publish prod website (http://gcpdiag.dev)
cd website
./hugo.sh
./hugo.sh deploy --target gcs-prod
