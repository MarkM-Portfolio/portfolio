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
# ----------------------------------------

BASE_DIR = os.getcwd()
print(f"📂 Current directory: {BASE_DIR}")

# --- Get list of local directories ---
local_dirs = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
if not local_dirs:
    print("⚠️ No local directories found to match GitHub repos.")
    exit(0)

deleted = False

# --- Delete only GitHub repos that exist locally ---
for repo_name in local_dirs:
    print(f"Checking GitHub repo: {BLGRE}{repo_name}{RES}...")
    repo_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}"
    response = requests.get(repo_url, headers=HEADERS)
    
    if response.status_code == 404:
        print(f"⚠️ Skipping {LGRE}{repo_name}{RES} ({RED}GitHub repo does not exist{RES})")
        continue

    print(f"🗑 Deleting {ORG_NAME}/{repo_name}...")
    del_resp = requests.delete(repo_url, headers=HEADERS)

    if del_resp.status_code in [204, 202]:
        print(f"✅ {DGRY}Deleted {LGRE}{repo_name}{RES}")
        deleted = True
    else:
        print(f"❌ Failed to delete {BLGRE}{repo_name}{RES} (HTTP {del_resp.status_code})")

if not deleted:
    print(f"⚠️ No GitHub repo found matching local directories in: {BASE_DIR}")
