#!/usr/bin/env .venv/bin/python

import os
from collections import namedtuple


# COLORS
RED='\033[31m'; GRE='\033[32m'; YEL='\033[33m'
BLU='\033[34m'; MAG='\033[35m'; CYN='\033[36m'
LGRY='\033[37m'; DGRY='\033[90m'; LRED='\033[91m'
LGRE='\033[92m'; LYEL='\033[93m'; LBLU='\033[94m'
LMAG='\033[95m'; LCYN='\033[96m'; WHTE='\033[97m'
BLNK='\033[5m'; NBLNK='\033[25m'; RES='\033[0m'
BLRED = '\033[1;91m'; BLGRE = '\033[1;92m'; BLYEL = '\033[1;93m'
BRED = '\033[1;91m'; BMAG = '\033[1;35m'; BYEL = '\033[1;33m'
BBLU = '\033[1;34m'; BGRE ='\033[1;32m'; BCYN = '\033[1;36m' 
BWHTE = '\033[1;97m'; BDGRY = '\033[1;90m'; BLGRY = '\033[1;37m'; 
BLMAG = '\033[1;95m'; BLBLU = '\033[1;94m'; BLCYN = '\033[1;96m'
CLEAR = '\033[H\033[J'; ORA = '\033[38;5;208m'

# GITHUB
ORG_NAME = "MarkM-Portfolio"
REMOTE_PREFIX = f"git@github.com:{ORG_NAME}"
USERNAME = [ "markmonmonteros", "markmon1919" ]
NAME = "Mark Monteros"
EMAIL = "markmon.monteros@proton.me"
BRANCH = "master"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, ".portfolio_gh_token")
SITE_DIR = "site"
EXCLUDE_REPOS = [ "sap-media-s3-bucket", "fork", "need_this", "portfolio", "BackUps" ]
EXCLUDE_PATHS = [ ".vscode", ".idea", ".DS_Store", "__pycache__", "*.log", ".git", ".venv", "node_modules", "bin", "build", "dist", ".terraform",
                 '.html', '.zip', '.tar', '.exe', '.dll', '.so', '.jpg', '.png', '.mp4', ".jar" ]
DEFAULT_LANG_MAP = { "py": "Python", "js": "JavaScript", "ts": "TypeScript", "java": "Java",
                    "go": "Golang", "rb": "Ruby", "php": "PHP", "sh": "Bash", "ps1": "Powershell", "bat": "CMD Batch",
                    "tf": "Terraform", "tfstate": "Terraform State File", "tfvars": "Terraform Var File",
                    "yml": "YAML", "yaml": "YAML", "json": "JSON", "html": "HTML", "gitattributes": "Git", "gitignore": "Git",
                    "css": "CSS", "cpp": "C++", "c": "C", "cs": "C#", "md": "Markdown", "inc": "AWS Infra",
                    "jinja": "Jinja", "tpl": "Template File", "txt": "Text File", "cfg": "Config File",
                    "Dockerfile": "Docker", "dockerignore": "Docker", "pem": "PEM Key"}
CV_FILE = "Mark Mon Monteros - CV (DevOps).pdf"