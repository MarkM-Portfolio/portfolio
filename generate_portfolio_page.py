#!/usr/bin/env bash

'''exec' "$(dirname "$0")/.venv/bin/python" "$0" "$@"
' '''


import os, requests, json
from config import (ORG_NAME, REMOTE_PREFIX, USERNAME, NAME, EMAIL, BRANCH, SCRIPT_DIR,
                    TOKEN_FILE, EXCLUDE_REPOS, EXCLUDE_PATHS, DEFAULT_LANG_MAP, SITE_DIR,
                    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, CV_FILE,
                    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU,
                    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES)

# --- TOKEN ---
if not os.path.isfile(TOKEN_FILE) or os.stat(TOKEN_FILE).st_size == 0:
    print(f"❌ GitHub token file missing or empty: {TOKEN_FILE}")
    GITHUB_TOKEN=os.getenv("GITHUB_TOKEN")
    print(f"Will use env var in pipeline: {GITHUB_TOKEN}")
    # exit(1)
else:
    with open(TOKEN_FILE, "r") as f:
        GITHUB_TOKEN = f.read().strip()

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.mercy-preview+json"  # topics API
}

# --- LANGUAGE COLORS ---
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Rust": "#dea584",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Dockerfile": "#0db7ed",
    "Terraform": "#844FBA",
    "Ansible": "#EE0000",
    "YAML": "#cb171e",
    "Kubernetes": "#326CE5",
    # ... full mapping if desired ...
}

CACHE_FILE = os.path.join(SCRIPT_DIR, ".contents_cache.json")
CONTENTS_CACHE = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        CONTENTS_CACHE = json.load(f)

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(CONTENTS_CACHE, f)

# --- FETCH REPO CONTENTS ---
def fetch_repo_contents(repo_full_name, refresh=False):
    if not refresh and repo_full_name in CONTENTS_CACHE:
        return CONTENTS_CACHE[repo_full_name]

    url = f"https://api.github.com/repos/{repo_full_name}/contents"
    resp = requests.get(url, headers=HEADERS)
    items = []
    if resp.status_code == 200 and isinstance(resp.json(), list):
        items = [i["name"].lower() for i in resp.json()]

    CONTENTS_CACHE[repo_full_name] = items
    save_cache()
    return items

# --- FETCH LANGUAGES ---
def fetch_languages(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return list(resp.json().keys())
    return []

# --- EXTRA LANGUAGE DETECTION ---
def detect_extra_languages(repo, refresh=False):
    extras = []
    name = repo["name"].lower()
    topics = [t.lower() for t in repo.get("topics", [])]
    items = fetch_repo_contents(repo["full_name"], refresh=refresh)

    def log_detect(lang):
        extras.append(lang)

    if any(k in name for k in ["docker", "container"]) or "docker" in topics or "dockerfile" in items:
        log_detect("Dockerfile")
    if any(k in name for k in ["terraform", "tf", "iac"]) or "terraform" in topics or any(f.endswith(".tf") for f in items):
        log_detect("Terraform")
    if "ansible" in name or "ansible" in topics or any(f in items for f in ["ansible.cfg", "playbook.yml", "playbook.yaml"]):
        log_detect("Ansible")
    if any(k in name for k in ["yaml", "yml"]) or "yaml" in topics or any(f.endswith((".yaml", ".yml")) for f in items):
        log_detect("YAML")
    if any(k in name for k in ["k8s", "kubernetes"]) or "kubernetes" in topics or "k8s" in topics or any(x in items for x in ["helm", "charts", "manifests"]):
        log_detect("Kubernetes")

    return list(set(extras))

# --- GENERATE INDEX ---
def generate_index(repos):
    os.makedirs(SITE_DIR, exist_ok=True)
    index_path = os.path.join(SITE_DIR, "index.html")

    # Load templates
    def load_template(name):
        with open(os.path.join("templates", name), "r", encoding="utf-8") as f:
            return f.read()

    style_html = load_template("style.html")
    search_html = load_template("search.html")
    header_html = load_template("header.html").replace("{ORG_NAME}", ORG_NAME).replace("{CV_FILE}", CV_FILE).replace("{SEARCH_COMPONENT}", search_html)
    base_start = load_template("base_start.html").replace("{ORG_NAME}", ORG_NAME).replace("{STYLE_HTML}", style_html).replace("{HEADER_HTML}", header_html)
    base_end = load_template("base_end.html")

    # Build page
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(base_start)

        for repo in repos:
            desc = repo.get("description") or "No description provided."
            stars = repo.get("stargazers_count", 0)
            topics = repo.get("topics", [])
            languages = repo.get("languages", [])

            f.write("<div class='card'>\n")
            f.write(f"<a href='{repo['html_url']}' target='_blank'>{repo['name']}</a>\n")
            f.write(f"<p class='desc'>{desc}</p>\n")
            f.write(f"<p class='stars'>⭐ {stars} stars</p>\n")

            if topics:
                f.write("<div class='topics'>\n")
                for t in topics:
                    f.write(f"<span class='topic'>{t}</span>\n")
                f.write("</div>\n")

            if languages:
                f.write("<div class='languages'>\n")
                for l in languages:
                    color = LANG_COLORS.get(l, "#6e7681")
                    f.write(f"<span class='lang' style='background:{color}'>{l}</span>\n")
                f.write("</div>\n")

            f.write("</div>\n")

        f.write(base_end)

# --- MAIN ---
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

def generate(data):
    print(f"Fetching repos for org: {LBLU}{ORG_NAME}{RES}...")
    repos = []
    for repo in data:
        if repo['name'].lower() in EXCLUDE_REPOS or 'practice' in repo['name'].lower():
            print(f"Exclude Repo --> {BLRED}{repo['name']}{RES}")
            continue
        print(f"Processing {BLGRE}{repo['name']}{RES}...")
        repo['languages'] = fetch_languages(repo['full_name'])
        repo['languages'] += detect_extra_languages(repo)
        repos.append(repo)
    repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)

    print(f"Found {YEL}{len(repos)}{RES} repos.")
    generate_index(repos)
    print(f"Generated {LMAG}index.html{RES} in {SITE_DIR}")

# def main():
#     print(f"Fetching repos for org: {LBLU}{ORG_NAME}{RES}...")
#     url = f"https://api.github.com/orgs/{ORG_NAME}/repos?per_page=100"
#     resp = requests.get(url, headers=HEADERS)

#     if resp.status_code == 200:
#         data = resp.json()
#         repos = []
#         for repo in data:
#             if repo['name'].lower() in EXCLUDE_REPOS:
#                 continue
#             print(f"Processing {BLGRE}{repo['name']}{RES}...")
#             repo['languages'] = fetch_languages(repo['full_name'])
#             repo['languages'] += detect_extra_languages(repo)
#             repos.append(repo)
#         repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
#     else:
#         print(f"❌ Failed to fetch repos: HTTP {resp.status_code}")
#         exit(1)

#     print(f"Found {YEL}{len(repos)}{RES} repos.")
#     generate_index(repos)
#     print(f"Generated {LMAG}index.html{RES} in {SITE_DIR}")

if __name__ == "__main__":
    # main()
    repos = get_all_repos(ORG_NAME)
    generate(data=repos)