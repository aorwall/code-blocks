import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def setup_github_repo(repo: str, base_commit: str, base_dir: str = "/tmp/repos") -> str:
    repo_name = get_repo_dir_name(repo)
    repo_url = f"git@github.com:{repo}.git"

    path = f"{base_dir}/{repo_name}"
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Directory '{path}' was created.")
    maybe_clone(repo_url, path)
    checkout_commit(path, base_commit)

    return path


def get_repo_dir_name(repo: str):
    return repo.replace("/", "_")


def maybe_clone(repo_url, repo_dir):
    if not os.path.exists(f"{repo_dir}/.git"):
        logger.info(f"Cloning repo '{repo_url}'")
        # Clone the repo if the directory doesn't exist
        result = subprocess.run(
            ["git", "clone", repo_url, repo_dir],
            check=True,
            text=True,
            capture_output=True,
        )

        if result.returncode == 0:
            logger.info(f"Repo '{repo_url}' was cloned to '{repo_dir}'")
        else:
            logger.info(f"Failed to clone repo '{repo_url}' to '{repo_dir}'")
            raise ValueError(f"Failed to clone repo '{repo_url}' to '{repo_dir}'")


def checkout_commit(repo_dir, commit_hash):
    subprocess.run(
        ["git", "reset", "--hard", commit_hash],
        cwd=repo_dir,
        check=True,
        text=True,
        capture_output=True,
    )
