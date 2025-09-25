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
    exit(1)

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
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ORG_NAME} Portfolio</title>
<style>
:root {{ --bg:#0d1117; --header-bg:#161b22; --text:#c9d1d9; --card-bg:#161b22; --border:#30363d; --link:#58a6ff; --desc:#8b949e; --stars:#a1a1aa; --topic-bg:#21262d; --lang-bg:#30363d; }}
body.light {{ --bg:#f9fafb; --header-bg:#24292f; --text:#333; --card-bg:#fff; --border:#e5e7eb; --link:#0366d6; --desc:#555; --stars:#777; --topic-bg:#eaf5ff; --lang-bg:#f3f4f6; }}
body {{ font-family:Arial,sans-serif; background:var(--bg); color:var(--text); margin:0; padding:0; transition:0.3s; }}
header {{ background:var(--header-bg); color:var(--text); padding:1.5rem; text-align:center; border-bottom:1px solid var(--border); }}
header h1 {{ margin:0; font-size:2rem; }}
.cv-button {{ display:block; margin:0.8rem auto 0 auto; background:gold; color:white; padding:0.4rem 0.8rem; border-radius:6px; border:1px solid white; text-decoration:none; font-size:0.9rem; width:max-content; }}
#toggle-btn {{ position:absolute; top:1.2rem; right:1rem; background:none; border:1px solid var(--border); color:var(--text); padding:0.4rem 0.8rem; border-radius:6px; cursor:pointer; font-size:0.9rem; }}
#search-box {{ width:100%; max-width:400px; padding:0.6rem 1rem; margin:1rem auto 0; display:block; border:1px solid var(--border); border-radius:6px; font-size:1rem; background:var(--card-bg); color:var(--text); }}
main {{ max-width:1100px; margin:2rem auto; padding:0 1rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:1.5rem; }}
.card {{ background:var(--card-bg); padding:1.2rem; border-radius:10px; border:1px solid var(--border); box-shadow:0 2px 6px rgba(0,0,0,0.2); transition:0.2s; }}
.card:hover {{ transform:translateY(-4px); box-shadow:0 6px 14px rgba(0,0,0,0.25); }}
.card a {{ text-decoration:none; font-weight:bold; color:var(--link); font-size:1.2rem; }}
.desc {{ margin:0.5rem 0 0.8rem; font-size:0.95rem; color:var(--desc); }}
.stars {{ font-size:0.85rem; color:var(--stars); margin-bottom:0.5rem; }}
.topics,.languages {{ margin-top:0.5rem; }}
.topic,.lang {{ display:inline-block; padding:0.2rem 0.6rem; margin:0 0.3rem 0.3rem 0; font-size:0.8rem; border-radius:20px; border:1px solid var(--border); }}
.lang {{ background:var(--lang-bg); }}
</style>
<script>
function toggleTheme() {{
    document.body.classList.toggle('light');
    localStorage.setItem('theme', document.body.classList.contains('light')?'light':'dark');
}}
window.onload=function() {{
    if(localStorage.getItem('theme')==='light') document.body.classList.add('light');
    const searchBox=document.getElementById('search-box');
    searchBox.addEventListener('input',function(){{
        const query=this.value.toLowerCase();
        document.querySelectorAll('.card').forEach(card=>{{ card.style.display=card.innerText.toLowerCase().includes(query)?'block':'none'; }});
    }});
}};
</script>
</head>
<body>
<header>
<h1>{ORG_NAME} Repositories</h1>
<a href="{CV_FILE}" download class="cv-button">📄 Download CV</a>
<button id="toggle-btn" onclick="toggleTheme()">🌙/☀️</button>
<input type="text" id="search-box" placeholder="Search repositories, topics, or languages...">
</header>
<main>
<div class="grid">
""")
        for repo in repos:
            desc = repo.get("description") or "No description provided."
            stars = repo.get("stargazers_count", 0)
            topics = repo.get("topics", [])
            languages = repo.get("languages", [])
            f.write(f"<div class='card'>\n")
            f.write(f"<a href='{repo['html_url']}' target='_blank'>{repo['name']}</a>\n")
            f.write(f"<p class='desc'>{desc}</p>\n")
            f.write(f"<p class='stars'>⭐ {stars} stars</p>\n")
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
        f.write("</div></main></body></html>")

# --- MAIN ---
def main():
    print(f"Fetching repos for org: {LBLU}{ORG_NAME}{RES}...")
    url = f"https://api.github.com/orgs/{ORG_NAME}/repos?per_page=100"
    resp = requests.get(url, headers=HEADERS)

    if resp.status_code == 200:
        data = resp.json()
        repos = []
        for repo in data:
            if repo['name'].lower() in EXCLUDE_REPOS:
                continue
            print(f"Processing {BLGRE}{repo['name']}{RES}...")
            repo['languages'] = fetch_languages(repo['full_name'])
            repo['languages'] += detect_extra_languages(repo)
            repos.append(repo)
        repos.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    else:
        print(f"❌ Failed to fetch repos: HTTP {resp.status_code}")
        exit(1)

    print(f"Found {YEL}{len(repos)}{RES} repos.")
    generate_index(repos)
    print(f"Generated {LMAG}index.html{RES} in {SITE_DIR}")

if __name__ == "__main__":
    main()
