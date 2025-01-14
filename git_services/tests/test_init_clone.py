import os
import shutil

import pytest

from git_services.cli import GitCLI
from git_services.init import errors
from git_services.init.clone import GitCloner
from git_services.init.config import User


@pytest.fixture
def test_user() -> User:
    return User(
        username="Test.Username",
        full_name="Test Name",
        email="test.uesername@email.com",
        oauth_token="TestSecretOauthToken123456",
    )


@pytest.fixture
def clone_dir(tmp_path):
    repo_dir = tmp_path / "clone"
    repo_dir.mkdir(parents=True, exist_ok=True)
    yield repo_dir
    shutil.rmtree(repo_dir, ignore_errors=True)


def test_simple_git_clone(test_user, clone_dir, mocker):
    git_url = "https://github.com"
    repo_url = "https://github.com/SwissDataScienceCenter/amalthea.git"
    mocker.patch("git_services.init.cloner.GitCloner._temp_plaintext_credentials", autospec=True)
    cloner = GitCloner(git_url=git_url, repo_url=repo_url, repo_directory=clone_dir, user=test_user)
    assert len(os.listdir(clone_dir)) == 0
    cloner.run(session_branch="main", root_commit_sha="test", s3_mounts=[])
    assert len(os.listdir(clone_dir)) != 0


def test_lfs_size_check(test_user, clone_dir, mocker):
    git_url = "https://github.com"
    repo_url = "https://github.com/SwissDataScienceCenter/amalthea.git"
    mocker.patch("git_services.init.cloner.GitCloner._temp_plaintext_credentials", autospec=True)
    mock_get_lfs_total_size_bytes = mocker.patch(
        "git_services.init.cloner.GitCloner._get_lfs_total_size_bytes", autospec=True
    )
    mock_disk_usage = mocker.patch("git_services.init.cloner.disk_usage", autospec=True)
    mock_get_lfs_total_size_bytes.return_value = 100
    mock_disk_usage.return_value = 0, 0, 10
    cloner = GitCloner(
        git_url=git_url,
        repo_url=repo_url,
        repo_directory=clone_dir,
        user=test_user,
        lfs_auto_fetch=True,
    )
    assert len(os.listdir(clone_dir)) == 0
    with pytest.raises(errors.NoDiskSpaceError):
        cloner.run(session_branch="main", root_commit_sha="test", s3_mounts=[])


@pytest.mark.parametrize(
    "lfs_lfs_files_output,expected_output",
    [('{"files": [{"size": 100}, {"size": 200}]}', 300), ('{"files": null}', 0)],
)
def test_lfs_output_parse(test_user, clone_dir, mocker, lfs_lfs_files_output, expected_output):
    git_url = "https://github.com"
    repo_url = "test"
    cloner = GitCloner(git_url=git_url, repo_url=repo_url, repo_directory=clone_dir, user=test_user)
    mock_cli = mocker.MagicMock(GitCLI, autospec=True)
    mock_cli.git_lfs.return_value = lfs_lfs_files_output
    cloner.cli = mock_cli
    assert cloner._get_lfs_total_size_bytes() == expected_output
