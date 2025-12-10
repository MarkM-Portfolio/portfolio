#!/usr/bin/env python3
# generate_site.py — async GitHub repo index generator with colors

import aiohttp, asyncio, os, json, time
from pathlib import Path
from typing import List, Dict, Any, Optional
from aiohttp import TCPConnector, ClientError, ClientConnectorError

# -------------------------------------------------
# CONFIG from your config.py
# -------------------------------------------------
from config import (
    ORG_NAME, REMOTE_PREFIX, USERNAME, NAME, EMAIL, BRANCH, SCRIPT_DIR,
    TOKEN_FILE, EXCLUDE_REPOS, EXCLUDE_PATHS, DEFAULT_LANG_MAP, SITE_DIR,
    LRED, LBLU, LCYN, LYEL, LMAG, LGRE, LGRY, RED, MAG, YEL, CV_FILE,
    GRE, CYN, BLU, WHTE, BLRED, BLYEL, BLGRE, BLMAG, BLBLU, ORA,
    BLCYN, BYEL, BMAG, BCYN, BWHTE, DGRY, BLNK, CLEAR, RES
)

# =================================================
# COLOR PRINT HELPERS (restored)
# =================================================
def p_info(msg): print(f"{LCYN}{msg}{RES}")
def p_good(msg): print(f"{LGRE}{msg}{RES}")
def p_warn(msg): print(f"{LYEL}{msg}{RES}")
def p_err(msg):  print(f"{LRED}{msg}{RES}")
def p_mag(msg):  print(f"{LMAG}{msg}{RES}")
def p_blue(msg): print(f"{LBLU}{msg}{RES}")

# =================================================
# TOKEN
# =================================================
if os.path.isfile(TOKEN_FILE) and os.stat(TOKEN_FILE).st_size > 0:
    with open(TOKEN_FILE, "r", encoding="utf-8") as tf:
        GITHUB_TOKEN = tf.read().strip()
        p_good(f"🔐 Loaded GitHub token from file: {TOKEN_FILE}")
else:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    p_warn("⚠️ TOKEN_FILE missing — using $GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github.mercy-preview+json",
    "Connection": "close"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# =================================================
# LANGUAGE COLORS
# =================================================
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
}

# =================================================
# CACHE
# =================================================
CACHE_FILE = os.path.join(SCRIPT_DIR, ".contents_cache.json")
CONTENTS_CACHE: Dict[str, List[str]] = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            CONTENTS_CACHE = json.load(f)
            p_info(f"📦 Loaded contents cache ({len(CONTENTS_CACHE)} repos)")
    except:
        p_warn("⚠️ Failed to load cache, starting empty")

def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(CONTENTS_CACHE, f, indent=2)
        p_good("💾 Saved cache")
    except:
        p_warn("⚠️ Failed saving cache")

# =================================================
# ASYNC HTTP HELPERS (WITH COLOR PRINTS)
# =================================================
MAX_ATTEMPTS = 5
BACKOFF_BASE = 1
CONCURRENT_CONNECTIONS = 20
REQUEST_TIMEOUT = 15

async def fetch_json(session: aiohttp.ClientSession, url: str, attempt: int = 1) -> Optional[Any]:
    try:
        async with session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT) as resp:

            # RATE LIMIT
            if resp.status == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                reset_ts = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait_for = max(0, reset_ts - int(time.time()))
                p_warn(f"🛑 RATE LIMIT — sleeping {wait_for}s → {url}")
                await asyncio.sleep(wait_for)
                return await fetch_json(session, url, attempt)

            if resp.status == 200:
                return await resp.json()

            p_warn(f"⚠️ HTTP {resp.status} for {url}")
            return None

    except (ClientConnectorError, ClientError, asyncio.TimeoutError) as e:
        if attempt < MAX_ATTEMPTS:
            backoff = BACKOFF_BASE * (2 ** (attempt - 1))
            p_warn(f"⚠️ Error: {e} — attempt {attempt}/{MAX_ATTEMPTS}, retry in {backoff}s → {url}")
            await asyncio.sleep(backoff)
            return await fetch_json(session, url, attempt + 1)

        p_err(f"❌ FAILED after {MAX_ATTEMPTS} attempts: {url} ({e})")
        return None

# =================================================
# FETCH REPO LIST
# =================================================
async def fetch_repo_list(session):
    repos = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.github.com/orgs/{ORG_NAME}/repos?per_page={per_page}&page={page}"
        p_blue(f"📄 Fetching repo page {page}…")
        data = await fetch_json(session, url)

        if not data:
            break

        repos.extend(data)
        if len(data) < per_page:
            break

        page += 1

    p_good(f"📦 Total repos fetched: {len(repos)}")
    return repos

# =================================================
# LANGUAGE + CONTENTS
# =================================================
async def fetch_languages(session, full_name):
    url = f"https://api.github.com/repos/{full_name}/languages"
    return list((await fetch_json(session, url)) or {})

async def fetch_contents(session, full_name):
    if full_name in CONTENTS_CACHE:
        return CONTENTS_CACHE[full_name]

    url = f"https://api.github.com/repos/{full_name}/contents"
    data = await fetch_json(session, url)

    items = []
    if isinstance(data, list):
        items = [i.get("name", "").lower() for i in data]

    CONTENTS_CACHE[full_name] = items
    save_cache()
    return items

# =================================================
# EXTRA LANG DETECTION
# =================================================
def detect_extra_languages(repo_name, topics, items):
    name = repo_name.lower()
    topics = [t.lower() for t in topics or []]
    extras = set()

    if "docker" in name or "dockerfile" in items: extras.add("Dockerfile")
    if "terraform" in name or any(f.endswith(".tf") for f in items): extras.add("Terraform")
    if "ansible" in name or "ansible.cfg" in items: extras.add("Ansible")
    if any(f.endswith((".yaml", ".yml")) for f in items): extras.add("YAML")
    if "k8s" in name or "helm" in items: extras.add("Kubernetes")

    return list(extras)

# =================================================
# PARALLEL REPO PROCESSING
# =================================================
async def process_repo(session, repo):
    name = repo["name"]
    full = repo["full_name"]

    p_info(f"🔧 Processing {name}…")

    languages_task = asyncio.create_task(fetch_languages(session, full))
    contents_task  = asyncio.create_task(fetch_contents(session, full))

    langs = await languages_task
    contents = await contents_task
    extras = detect_extra_languages(name, repo.get("topics", []), contents)

    repo["languages"] = list(dict.fromkeys((langs or []) + extras))  # unique

    p_good(f"✔ Done → {name}")
    return repo

# =================================================
# HTML GENERATION
# =================================================
def generate_index(repos):
    os.makedirs(SITE_DIR, exist_ok=True)
    index_path = os.path.join(SITE_DIR, "index.html")

    def load_template(name):
        with open(os.path.join("templates", name), "r", encoding="utf-8") as f:
            return f.read()

    styles = load_template("styles.css")
    search = load_template("search.html")

    header = load_template("header.html") \
        .replace("{ORG_NAME}", ORG_NAME) \
        .replace("{CV_FILE}", CV_FILE) \
        .replace("{SEARCH_COMPONENT}", search)

    footer = load_template("footer.html") \
        .replace("{ORG_NAME}", ORG_NAME) \
        .replace("{EMAIL}", EMAIL) \
        .replace("{GH_USERNAME}", USERNAME[1]) \
        .replace("{USERNAME}", USERNAME[0])

    base_start = load_template("base_start.html") \
        .replace("{ORG_NAME}", ORG_NAME) \
        .replace("{STYLES_CSS}", styles) \
        .replace("{HEADER_HTML}", header)

    base_end = load_template("base_end.html") \
        .replace("{FOOTER_HTML}", footer)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(base_start)

        for repo in repos:
            name = repo["name"]
            p_good(f"📌 Writing card {WHTE}→ {ORA}{name}{RES}")

            desc = repo.get("description", "No description provided.")
            stars = repo.get("stargazers_count", 0)
            topics = repo.get("topics", [])
            languages = repo.get("languages", [])

            f.write(f"""
<a class="card-link" href="{repo['html_url']}" target="_blank" rel="noopener">
  <div class="card">
    <div class="card-title">{name}</div>
    <p class="desc">{desc}</p>
    <p class="stars">⭐ {stars} stars</p>
""")

            if topics:
                f.write("    <div class='topics'>\n")
                for t in topics:
                    f.write(f"      <span class='topic'>{t}</span>\n")
                f.write("    </div>\n")

            if languages:
                f.write("    <div class='languages'>\n")
                for l in languages:
                    color = LANG_COLORS.get(l, "#6e7681")
                    f.write(f"      <span class='lang' style='background:{color}'>{l}</span>\n")
                f.write("    </div>\n")

            f.write("  </div>\n</a>\n")

        f.write(base_end)

    p_mag(f"🎉 Index generated → {index_path}")

# =================================================
# MAIN ASYNC RUNNER
# =================================================
async def main_async():
    p_mag(f"🚀 START: Building portfolio for {ORG_NAME}")

    connector = TCPConnector(limit=CONCURRENT_CONNECTIONS, force_close=True)
    timeout = aiohttp.ClientTimeout(sock_connect=REQUEST_TIMEOUT, sock_read=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        repos = await fetch_repo_list(session)
        if not repos:
            p_err("❌ No repos fetched. Aborting.")
            return

        filtered = [
            r for r in repos
            if r["name"].lower() not in (name.lower() for name in EXCLUDE_REPOS)
            and "practice" not in r["name"].lower()
        ]

        p_info(f"🧮 {len(filtered)} repos to process (parallel {CONCURRENT_CONNECTIONS})")

        sem = asyncio.Semaphore(CONCURRENT_CONNECTIONS)

        async def guarded(repo):
            async with sem:
                return await process_repo(session, repo)

        tasks = [asyncio.create_task(guarded(r)) for r in filtered]

        completed = []
        for t in asyncio.as_completed(tasks):
            try:
                completed.append(await t)
            except Exception as e:
                p_err(f"❌ Error in repo task: {e}")
                
        completed.sort(key=lambda x: x["name"].lower())

        generate_index(completed)

    p_good("🎯 DONE")
    
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
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        p_err("Interrupted by user.")
        