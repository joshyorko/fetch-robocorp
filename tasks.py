import os
import subprocess
import shutil
import json
import pathlib
import zipfile
from robocorp import task, workitems
from robocorp.tasks import get_output_dir # Keep this if repos task is kept
import pandas as pd # Keep this if repos task is kept
from git import Repo # Keep this if repos task is kept
from git.exc import GitCommandError # Keep this if repos task is kept
from fetch_repos import fetch_github_repos # Keep this if repos task is kept

# ---------- NEW: local FileAdapter ----------
os.environ["RC_WORKITEM_ADAPTER"] = "FileAdapter"
os.environ["RC_WORKITEM_INPUT_PATH"]  = "/tmp/input.json"
os.environ["RC_WORKITEM_OUTPUT_PATH"] = "/tmp/output.json"

@task
def repos():
    """Fetches the list of repositories from GitHub and saves it to a CSV file."""
    for item in workitems.inputs:
        org = item.payload.get("org")
        if not org:
            raise ValueError("Organization name is required in the payload.")
        print(f"Fetching repositories for organization: {org}")
        break
    return fetch_github_repos(org)

# ---------- PRODUCER ----------
@task
def producer():
    """Read repos.txt and emit one work item per repo URL."""
    repos = pathlib.Path("repos.txt").read_text().splitlines()
    for repo in filter(None, map(str.strip, repos)):
        wi = workitems.outputs.create()
        wi.payload = {"repo": repo}

# ---------- CONSUMER ----------
@task
def consumer():
    """Clone repo, zip it, attach as file."""
    workspace = pathlib.Path("/tmp/workspace")
    workspace.mkdir(parents=True, exist_ok=True)

    for wi in workitems.inputs:
        url = wi.payload["repo"]
        name = url.rsplit("/", 1)[-1].replace(".git", "")
        repo_dir = workspace / name
        subprocess.run(["git", "clone", "--depth", "1", url, str(repo_dir)],
                       check=True)
        zip_path = workspace / f"{name}.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for p in repo_dir.rglob("*"):
                zf.write(p, p.relative_to(repo_dir))
        wi.files.add_local_file("archive", zip_path)
        wi.done()
        shutil.rmtree(repo_dir)
