import requests
import pandas as pd

def fetch_github_repos(org="robocorp"):
    url = f"https://api.github.com/orgs/{org}/repos"
    per_page = 100
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    repo_list = []
    page = 1

    while True:
        params = {
            "per_page": per_page,
            "page": page,
            "sort": "updated",
            "direction": "desc"
        }
        response = requests.get(url, headers=headers, params=params)
        
        # Handle rate limiting
        if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
            print("Rate limit exceeded. Please try again later.")
            break
            
        if response.status_code != 200:
            print(f"Failed to fetch repositories on page {page}: {response.status_code}")
            break

        repos = response.json()
        if not repos:  # No more repos to fetch
            break

        for repo in repos:
            if not repo.get("private", True):  # Only include public repos
                repo_list.append({
                    "Name": repo.get("name"),
                    "Description": repo.get("description"),
                    "Language": repo.get("language"),
                    "Stars": repo.get("stargazers_count"),
                    "URL": repo.get("html_url"),
                    "Created": repo.get("created_at"),
                    "Last Updated": repo.get("updated_at"),
                    "Is Fork": repo.get("fork", False)
                })

        print(f"Fetched page {page} with {len(repos)} repositories. Total fetched so far: {len(repo_list)}")
        
        # If we got fewer repos than per_page, we've reached the end
        if len(repos) < per_page:
            break
        page += 1

    print(f"\nRepository statistics:")
    print(f"Total public repositories found: {len(repo_list)}")
    
    # Sort by stars for the CSV
    repo_list.sort(key=lambda x: x["Stars"] or 0, reverse=True)
    
    csv_filename = f"devdata/work-items-in/test-input-for-producer/repos.csv"
    df = pd.DataFrame(repo_list)
    df.to_csv(csv_filename, index=False)
    print(f"CSV file '{csv_filename}' created successfully with {len(repo_list)} repositories.")

if __name__ == "__main__":
    import sys
    org = sys.argv[1] if len(sys.argv) > 1 else "robocorp"
    fetch_github_repos(org)
