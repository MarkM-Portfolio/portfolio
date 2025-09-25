#!/usr/bin/env bash
'''exec' "$(dirname "$0")/.venv/bin/python" "$0" "$@"
' '''

import os, subprocess, requests
from config import (ORG_NAME, REMOTE_PREFIX, USERNAME, NAME, EMAIL, BRANCH, SCRIPT_DIR,
                    TOKEN_FILE, EXCLUDE_REPOS, EXCLUDE_PATHS, DEFAULT_LANG_MAP, SITE_DIR,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL,
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU,
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)


# --- GitHub token ---
if not os.path.isfile(TOKEN_FILE) or os.stat(TOKEN_FILE).st_size == 0:
    print(f"❌ GitHub token file missing or empty: {TOKEN_FILE}")
    exit(1)

with open(TOKEN_FILE) as f:
    GITHUB_TOKEN = f.read().strip()

HEADERS = { 
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.mercy-preview+json"
}

BASE_DIR = os.getcwd()
PARENT_FOLDER = os.path.basename(BASE_DIR)
HAS_GIT_LFS = subprocess.call(["which", "git-lfs"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
if not HAS_GIT_LFS:
    print("⚠️ git-lfs not installed. Large files won't be automatically tracked.")

# --- Helper functions ---
def run(cmd, cwd=None, timeout=None):
    try:
        process = subprocess.Popen(cmd, shell=True, cwd=cwd,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(f"{DGRY}{line.rstrip()}{RES}")
        process.wait(timeout=timeout)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
    except subprocess.TimeoutExpired:
        print(f"⚠️ Command timed out: {cmd}")
        process.kill()

def remove_git_history(repo):
    git_dir = os.path.join(repo, ".git")
    if os.path.exists(git_dir):
        subprocess.run(f"rm -rf {git_dir}", shell=True)
    run("git init", cwd=repo)
    run(f"git config user.name '{BLCYN}{USERNAME}{RES}'", cwd=repo)
    run(f"git config user.email '{BLBLU}{EMAIL}{RES}'", cwd=repo)
    try:
        subprocess.run(["git", "checkout", "-b", BRANCH], cwd=repo)
    except subprocess.CalledProcessError: pass

def add_gitignore(repo):
    gitignore_path = os.path.join(repo, ".gitignore")
    existing = set()
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            existing.update(line.strip().rstrip("/") for line in f if line.strip())
    new_paths = [p.rstrip("/") for p in EXCLUDE_PATHS if p.rstrip("/") not in existing]
    if new_paths:
        with open(gitignore_path, "a") as f:
            for line in sorted(new_paths):
                f.write(line + "\n")

# --- Add gitattributes with Docker Compose, Ansible, Kubernetes ---
def add_gitattributes(repo):
    gitattributes_path = os.path.join(repo, ".gitattributes")
    lines = set()
    for root, _, files in os.walk(repo):
        if ".git" in root: continue
        for f in files:
            path = os.path.join(root, f)
            # Skip missing files (dynamic links or broken symlinks)
            if not os.path.exists(path):
                print(f"⚠️ Skipping missing file: {path}")
                continue
            f_lower = f.lower()
            # Docker
            if f == "Dockerfile" or f_lower in ["docker-compose.yml", "docker-compose.yaml"]:
                lines.add(f"{f} linguist-language=Docker linguist-vendored=false")
            # Terraform
            elif f_lower.endswith(".tf"):
                lines.add("*.tf linguist-language=Terraform linguist-vendored=false")
            # Ansible
            elif f_lower.endswith((".yml", ".yaml")) and any(p in root for p in ["roles","tasks","molecule"]):
                lines.add(f"**/{f} linguist-language=Ansible linguist-vendored=false")
            # Kubernetes
            elif f_lower.endswith((".yml", ".yaml")) and any(p in root for p in ["k8s","manifests","deploy","charts","helm"]):
                lines.add(f"**/{f} linguist-language=Kubernetes linguist-vendored=false")
            # Other YAML
            elif f_lower.endswith((".yml",".yaml")):
                lines.add(f"*.yml linguist-language=YAML linguist-vendored=false")
            # Other extensions
            elif "." in f:
                ext = f.split(".")[-1].lower()
                lang = DEFAULT_LANG_MAP.get(ext, ext.capitalize())
                lines.add(f"*.{ext} linguist-language={lang} linguist-vendored=false")
    with open(gitattributes_path, "w") as f:
        for line in sorted(lines):
            f.write(line + "\n")
    run("git add -f .gitattributes", cwd=repo)

# --- Language stats ---
def calculate_language_stats(repo):
    lang_sizes = {}
    for root, _, files in os.walk(repo):
        if ".git" in root: continue
        for f in files:
            path = os.path.join(root, f)
            # Skip missing files (dynamic links or broken symlinks)
            if not os.path.exists(path):
                print(f"⚠️ Skipping missing file: {path}")
                continue
            size = os.stat(path).st_size
            f_lower = f.lower()
            # Docker
            if f == "Dockerfile" or f_lower in ["docker-compose.yml", "docker-compose.yaml"]:
                lang = "Docker"
            # Terraform
            elif f_lower.endswith(".tf"):
                lang = "Terraform"
            # Ansible
            elif f_lower.endswith((".yml", ".yaml")) and any(p in root for p in ["roles","tasks","molecule"]):
                lang = "Ansible"
            # Kubernetes
            elif f_lower.endswith((".yml", ".yaml")) and any(p in root for p in ["k8s","manifests","deploy","charts","helm"]):
                lang = "Kubernetes"
            # Other YAML
            elif f_lower.endswith((".yml",".yaml")):
                lang = "YAML"
            # Other extensions
            elif "." in f:
                ext = f.split(".")[-1].lower()
                lang = DEFAULT_LANG_MAP.get(ext, ext.capitalize())
            else:
                continue
            lang_sizes[lang] = lang_sizes.get(lang, 0) + size
    total = sum(lang_sizes.values())
    if total == 0: return {}
    return {lang: round(size / total * 100, 2) for lang, size in lang_sizes.items()}

# --- Git LFS ---
def track_git_lfs(repo):
    if not HAS_GIT_LFS:
        print("⚠️ git-lfs not installed. Large files won't be automatically tracked.")
        return

    lfs_tracked = []
    for root, _, files in os.walk(repo):
        if ".git" in root: continue
        for f in files:
            path = os.path.join(root, f)
            if not os.path.exists(path):
                print(f"⚠️ Skipping missing file: {path}")
                continue
            size = os.stat(path).st_size
            rel_path = os.path.relpath(path, repo)
            # Track files between 50 MB and 2 GB
            if 50*1024*1024 < size <= 2*1024*1024*1024:
                run(f"git lfs track '{rel_path}'", cwd=repo)
                lfs_tracked.append(rel_path)
            # Ignore files >2 GB
            elif size > 2*1024*1024*1024:
                print(f"⚠️ Skipping file >2GB: {rel_path}")
                with open(os.path.join(repo, ".gitignore"), "a") as g:
                    g.write(rel_path + "\n")

    # Add .gitattributes if any LFS files
    if lfs_tracked:
        run("git add .gitattributes", cwd=repo)

def ensure_empty_dirs(repo):
    for root, dirs, _ in os.walk(repo):
        for d in dirs:
            dir_path = os.path.join(root,d)
            if not os.listdir(dir_path):
                keep_file = os.path.join(dir_path,".gitkeep")
                if not os.path.exists(keep_file): open(keep_file,"w").close()

def initial_commit(repo, repo_name):
    readme = os.path.join(repo,"README.md")
    if not os.path.exists(readme):
        with open(readme,"w") as f: f.write(f"# {repo_name}\n")
    run("git add -A", cwd=repo)
    try:
        run("git commit -m 'Initial commit with clean history, .gitignore, .gitattributes, LFS'", cwd=repo)
    except subprocess.CalledProcessError: pass

def create_github_repo(repo_name):
    url=f"https://api.github.com/repos/{ORG_NAME}/{repo_name}"
    r=requests.get(url,headers=HEADERS)
    if r.status_code==404:
        data={"name":repo_name,"private":True,"default_branch":BRANCH}
        r2=requests.post(f"https://api.github.com/orgs/{ORG_NAME}/repos",headers=HEADERS,json=data)
        if r2.status_code==201: print(f"✅ Repo {LGRE}{repo_name}{RES} created successfully as private.")
        else: print(f"❌ Failed to create repo {LGRE}{repo_name}{RES} (HTTP {r2.status_code})"); return False
    else: print(f"✅ Repo {BLGRE}{repo_name}{RES} already exists on GitHub.")
    return True

# --- Push safely ---
def set_remote_and_push(repo, repo_name):
    """
    Safely set Git remote and push branch + tags to GitHub.
    Handles Git LFS, skips files >2GB, and uses timeouts.
    """
    remote = f"{REMOTE_PREFIX}/{repo_name}.git"

    # Remove existing origin if present
    try:
        result = subprocess.run("git remote", shell=True, capture_output=True, text=True, cwd=repo)
        if "origin" in result.stdout.split():
            run("git remote remove origin", cwd=repo)
    except subprocess.CalledProcessError:
        pass

    # Add SSH remote
    run(f"git remote add origin {remote}", cwd=repo)
    print(f"🔗 Remote set to: {LCYN}{remote}{RES}")

    # Ensure LFS installed
    if HAS_GIT_LFS:
        run("git lfs install", cwd=repo)

    # Commit any uncommitted LFS changes
    try:
        run("git add -A", cwd=repo)
        run("git commit -m 'Track large files with Git LFS' || true", cwd=repo)
    except subprocess.CalledProcessError:
        pass

    # Push branch first
    try:
        run(f"git push -u origin {BRANCH}", cwd=repo, timeout=600)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to push branch {BRANCH}: {e}")
    except subprocess.TimeoutExpired:
        print(f"⚠️ Push timed out for branch {BRANCH}")

    # Push tags separately
    try:
        run("git push --tags origin", cwd=repo, timeout=600)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to push tags: {e}")
    except subprocess.TimeoutExpired:
        print(f"⚠️ Push timed out for tags")

    print(f"✅ Push completed for {repo_name} (branch + tags)")

def sanitize_topic(t):
    t = t.lower().strip().replace(" ","-")
    t = ''.join(c for c in t if c.isalnum() or c=='-')
    return t.strip("-")[:50]

def add_topics(repo_name):
    topics=[sanitize_topic(PARENT_FOLDER)]
    url=f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/topics"
    resp=requests.put(url,headers=HEADERS,json={"names":topics})
    if resp.status_code in (200,201): print(f"🏷️ Topics added to {LGRE}{repo_name}{RES}: {topics}")
    else: print(f"❌ Failed to add topics to {LGRE}{repo_name}{RES}: HTTP {resp.status_code}, {resp.text}")

# --- Main Loop ---
local_dirs=[d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR,d))]

for repo in local_dirs:
    repo_name = os.path.basename(repo)
    if repo_name in EXCLUDE_REPOS:
        print(f"⏭ Skipping {repo_name}")
        continue
    print(f"📦 Processing {BLGRE}{repo_name}{RES} (path: {repo})")

    remove_git_history(repo)     # clean history
    add_gitignore(repo)          # ignore unwanted paths
    track_git_lfs(repo)          # track large files before committing
    add_gitattributes(repo)      # write gitattributes after LFS
    ensure_empty_dirs(repo)      # keep empty dirs
    initial_commit(repo, repo_name)  # commit everything

    stats = calculate_language_stats(repo)
    if stats:
        print(f"📊 {CYN}Estimated language percentages{RES}:")
        for lang, pct in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {YEL}{lang}{RES}: {MAG}{pct}{WHTE}%{RES}")
    else:
        print(f"📊 {LRED}No recognizable language files found{RES}.")

    if not create_github_repo(repo_name): continue
    set_remote_and_push(repo, repo_name)
    add_topics(repo_name)

print(f"🎉 {BLYEL}All repos processed.{RES}")

