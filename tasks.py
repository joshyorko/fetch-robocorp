from pathlib import Path
from robocorp import workitems
from robocorp.tasks import get_output_dir, task
import pandas as pd
import shutil
import os
import git
from git import Repo
from git.exc import GitCommandError
from fetch_repos import fetch_github_repos




def repos():
    """Fetches the list of repositories from GitHub and saves it to a CSV file."""
    for item in workitems.inputs:
        payload = item.payload
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")
        org = payload.get("org")
        if not org:
            raise ValueError("Organization name is required in the payload.")
        print(f"Fetching repositories for organization: {org}")
        break
    return fetch_github_repos(org)

@task
def producer():
    """Split Csv rows into multiple output Work Items for the next step."""
    output = get_output_dir() or Path("output")
    
    # Get the DataFrame from repos() function
    df = repos()
    
    outputs_created = False
    
    if df is not None and not df.empty:
        print(f"Processing {len(df)} repositories from DataFrame")
        rows = df.to_dict(orient="records")
        for row in rows:
            payload = {
                "Name": row.get("Name"),
                "URL": row.get("URL"),
                "Description": row.get("Description"),
                "Created": row.get("Created"),
                "Last Updated": row.get("Last Updated"),
                "Language": row.get("Language"),
                "Stars": row.get("Stars"),
                "Is Fork": row.get("Is Fork")
            }
            workitems.outputs.create(payload)
            outputs_created = True
        print(f"Created {len(rows)} work items from DataFrame")
    else:
        print("No data received from repos() function")
    
    if not outputs_created:
        print("No output work items were created. Check if repos() returned valid data.")


@task
def consumer():
    """Clones all the repositories from the input Work Items and zips them and saves them to the output directory."""
    output = get_output_dir() or Path("output")
    filename = "repos.zip"
    repos_dir = output / "repos"
    output_path = output / filename

    # Create output directories if they don't exist
    repos_dir.mkdir(parents=True, exist_ok=True)
    
    for item in workitems.inputs:
        try:
            payload = item.payload
            if not isinstance(payload, dict):
                print(f"Skipping item with non-dict payload: {payload}")
                item.fail("APPLICATION", code="INVALID_PAYLOAD", message="Payload is not a dict.")
                continue
            url = payload.get("URL")
            if not url:
                print(f"Skipping item with missing URL: {payload}")
                item.fail("APPLICATION", code="MISSING_URL", message="URL is missing in payload.")
                continue
            repo_name = url.split('/')[-1].replace('.git', '')
            repo_path = repos_dir / repo_name
            print(f"Cloning repository: {repo_name}")
            
            try:
                # Clone with GitPython, showing progress (if supported)
                Repo.clone_from(url, repo_path)
                print(f"Successfully cloned: {repo_name}")
                item.done()
            except GitCommandError as git_err:
                error_msg = f"Git error while cloning {repo_name}: {str(git_err)}"
                print(error_msg)
                item.fail("BUSINESS", code="GIT_ERROR", message=error_msg)
                continue
                
        except AssertionError as err:
            item.fail("BUSINESS", code="INVALID_ORDER", message=str(err))
        except KeyError as err:
            item.fail("APPLICATION", code="MISSING_FIELD", message=str(err))
    
    # Get all directories that are git repositories in the repos directory
    git_repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d)) 
                 and os.path.exists(os.path.join(repos_dir, d, '.git'))]
    
    if git_repos:
        print(f"Creating zip archive of {len(git_repos)} repositories...")
        try:
            # Create the zip file containing all repositories
            shutil.make_archive(str(output_path.with_suffix('')), 'zip', 
                              root_dir=str(repos_dir), base_dir=None)
            print(f"Successfully created archive at: {output_path}")
            
            # Clean up: remove the cloned repositories after zipping
            print("Cleaning up cloned repositories...")
            shutil.rmtree(repos_dir)
            print("Cleanup complete")
        except Exception as e:
            print(f"Error during archive creation or cleanup: {str(e)}")
            raise

