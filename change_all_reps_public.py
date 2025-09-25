#!/usr/bin/env bash
'''exec' "$(dirname "$0")/.venv/bin/python" "$0" "$@"
' '''

import os, requests
from config import (ORG_NAME, REMOTE_PREFIX, USERNAME, NAME, EMAIL, BRANCH, SCRIPT_DIR,
                    TOKEN_FILE, EXCLUDE_REPOS, EXCLUDE_PATHS, DEFAULT_LANG_MAP, SITE_DIR,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL,
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU,
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)


# --- TOKEN ---
if not os.path.isfile(TOKEN_FILE) or os.stat(TOKEN_FILE).st_size == 0:
    print(f"❌ GitHub token file missing or empty: {TOKEN_FILE}")
    exit(1)

with open(TOKEN_FILE) as f:
    GITHUB_TOKEN = f.read().strip()

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --- Pagination support ---
def get_all_repos(org_name):
    repos = []
    page = 1
    per_page = 100
    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?per_page={per_page}&page={page}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print("Failed to fetch repos:", resp.status_code, resp.text)
            break
        page_repos = resp.json()
        if not page_repos:
            break
        repos.extend(page_repos)
        page += 1
    return repos

# --- Fetch all repos ---
repos = get_all_repos(ORG_NAME)

# --- Make private repos public ---
for repo in repos:
    if isinstance(repo, dict) and repo.get("private"):
        name = repo["name"]
        url = f"https://api.github.com/repos/{ORG_NAME}/{name}"
        patch_resp = requests.patch(url, headers=HEADERS, json={"private": False})
        if patch_resp.status_code == 200:
            print(f"✅ Made '{name}' public")
        else:
            print(f"❌ Failed to make '{name}' public:", patch_resp.json())