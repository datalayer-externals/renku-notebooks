# -*- coding: utf-8 -*-
#
# Copyright 2019 - Swiss Data Science Center (SDSC)
# A partnership between École Polytechnique Fédérale de Lausanne (EPFL) and
# Eidgenössische Technische Hochschule Zürich (ETHZ).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Mocks and fixtures that are loaded automatically by pytest.
"""
import os
from unittest.mock import MagicMock
import pytest
import base64
import json

from tests.utils.classes import AttributeDictionary


os.environ["GITLAB_URL"] = "https://gitlab-url.com"
os.environ["IMAGE_REGISTRY"] = "registry.gitlab-url.com"
os.environ["DEFAULT_IMAGE"] = "renku/singleuser:latest"
os.environ[
    "NOTEBOOKS_SERVER_OPTIONS_DEFAULTS_PATH"
] = f"{os.getcwd()}/tests/unit/dummy_server_defaults.json"
os.environ[
    "NOTEBOOKS_SERVER_OPTIONS_UI_PATH"
] = f"{os.getcwd()}/tests/unit/dummy_server_options.json"
os.environ["SESSION_INGRESS_ANNOTATIONS"] = "{}"


@pytest.fixture
def app():
    os.environ[
        "NOTEBOOKS_SERVER_OPTIONS_DEFAULTS_PATH"
    ] = "tests/unit/dummy_server_defaults.json"
    os.environ[
        "NOTEBOOKS_SERVER_OPTIONS_UI_PATH"
    ] = "tests/unit/dummy_server_options.json"
    from renku_notebooks.wsgi import app

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def git_params():
    url = "git_url"
    auth_header = "Bearer token"
    return {url: {"AuthorizationHeader": auth_header}}


@pytest.fixture
def parsed_jwt():
    return {
        "sub": "userid",
        "email": "email",
        "iss": "oidc_issuer",
    }


@pytest.fixture
def proper_headers(parsed_jwt, git_params):
    return {
        "Renku-Auth-Id-Token": ".".join(
            [
                base64.b64encode(json.dumps({}).encode()).decode(),
                base64.b64encode(json.dumps(parsed_jwt).encode()).decode(),
                base64.b64encode(json.dumps({}).encode()).decode(),
            ]
        ),
        "Renku-Auth-Git-Credentials": base64.b64encode(
            json.dumps(git_params).encode()
        ).decode(),
        "Renku-Auth-Access-Token": "test",
    }


@pytest.fixture
def gitlab_projects():
    return AttributeDictionary({})


@pytest.fixture(autouse=True)
def gitlab(mocker, gitlab_projects):
    gitlab = mocker.patch("renku_notebooks.api.classes.user.Gitlab")
    gitlab_mock = MagicMock()
    gitlab_mock.auth = MagicMock()
    gitlab_mock.projects = gitlab_projects
    gitlab_mock.namespace = "namespace"
    gitlab_mock.user = AttributeDictionary(
        {"username": "namespace", "name": "John Doe"}
    )
    gitlab.return_value = gitlab_mock
    return gitlab


@pytest.fixture
def make_all_images_valid(mocker):
    mocker.patch("renku_notebooks.api.classes.server.image_exists").return_value = True
    mocker.patch("renku_notebooks.api.classes.server.get_docker_token").return_value = (
        "token",
        False,
    )


@pytest.fixture
def make_server_args_valid(mocker):
    mocker.patch(
        "renku_notebooks.api.notebooks.UserServer._project_exists"
    ).return_value = True
    mocker.patch(
        "renku_notebooks.api.notebooks.UserServer._branch_exists"
    ).return_value = True
    mocker.patch(
        "renku_notebooks.api.notebooks.UserServer._commit_sha_exists"
    ).return_value = True