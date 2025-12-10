#!/usr/bin/env bash
set -euo pipefail

###########################################
# Prompt helper with default fallback
###########################################
prompt() {
  local varname="$1"
  local prompt_text="$2"
  local default="$3"
  local input

  if [ -n "$default" ]; then
    read -r -p "$prompt_text [$default]: " input
    input="${input:-$default}"
  else
    read -r -p "$prompt_text: " input
  fi

  printf -v "$varname" "%s" "$input"
}

###########################################
# Interactive Prompts (ONLY these three)
###########################################
DEFAULT_DATE="$(date '+%d %b %Y')"
DEFAULT_ROLE="DevOps Engineer"

echo "=== Cover Letter Generator ==="
prompt DATE "Date" "$DEFAULT_DATE"
prompt COMPANY "Company name" ""
prompt ROLE "Role / Job title" "$DEFAULT_ROLE"

###########################################
# FIXED CONTACT INFO (NO PROMPTS)
###########################################
MOBILE="+63 994 741 9641"
EMAIL="markmon.monteros@proton.me"
WEBSITE="https://markmonmonteros.site"

###########################################
# Template + Filename Sanitization
###########################################
TEMPLATE="cover-letter.tpl"

CLEAN_COMPANY=$(echo "$COMPANY" \
  | sed 's/^[ \t]*//;s/[ \t]*$//' \
  | tr '[:space:]' '-' \
  | tr -cd '[:alnum:]-' \
  | sed 's/-\{2,\}/-/g' \
  | sed 's/^-//; s/-$//')

TXT_OUTPUT="cover-letter_${CLEAN_COMPANY}.txt"
HTML_TEMP="cover-letter_${CLEAN_COMPANY}.html"
PDF_OUTPUT="cover-letter_${CLEAN_COMPANY}.pdf"

###########################################
# Check Template
###########################################
if [[ ! -f "$TEMPLATE" ]]; then
  echo "ERROR: Missing template: $TEMPLATE"
  exit 1
fi

###########################################
# Generate TXT From Template
###########################################
sed \
  -e "s|\${DATE}|$DATE|g" \
  -e "s|\${COMPANY}|$COMPANY|g" \
  -e "s|\${ROLE}|$ROLE|g" \
  -e "s|\${MOBILE}|$MOBILE|g" \
  -e "s|\${EMAIL}|$EMAIL|g" \
  -e "s|\${WEBSITE}|$WEBSITE|g" \
  "$TEMPLATE" > ${TXT_OUTPUT}

##############################
# Create DIV_CONTENT but allow <strong> and links (<mailto:...>, <http(s)://...>)
##############################

# 1) Read original TXT, temporarily protect allowed tags by placeholders
TMP="$(mktemp)"
sed -E \
  -e 's|<strong>|__STRONG_OPEN__|g' \
  -e 's|</strong>|__STRONG_CLOSE__|g' \
  -e 's|<em>|__EM_OPEN__|g' \
  -e 's|</em>|__EM_CLOSE__|g' \
  "$TXT_OUTPUT" > "$TMP"

# 2) Escape all HTML special chars (so user input is safe)
ESCAPED=$(sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' "$TMP")

# 3) Restore allowed tags
ESCAPED=$(printf '%s' "$ESCAPED" \
  | sed -E \
    -e 's|__STRONG_OPEN__|<strong>|g' \
    -e 's|__STRONG_CLOSE__|</strong>|g' \
    -e 's|__EM_OPEN__|<em>|g' \
    -e 's|__EM_CLOSE__|</em>|g')

# 4) Convert escaped angle-bracket links like &lt;mailto:...&gt; and &lt;https://...&gt; into <a href="...">...</a>
#    This expects your template uses <mailto:...> and <https://...> exactly.
ESCAPED=$(printf '%s' "$ESCAPED" \
  | sed -E \
    -e 's|&lt;mailto:([^&]*)&gt;|<a href="mailto:\1">\1</a>|g' \
    -e 's|&lt;(https?://[^&]*)&gt;|<a href="\1">\1</a>|g')

# 5) Wrap each line into a <div> to preserve spacing and allow justification
DIV_CONTENT=$(printf '%s' "$ESCAPED" | awk '{ print "<div>" $0 "</div>" }')

# remove temp file
rm -f "$TMP"

# 6) create final HTML (this keeps your existing CSS for single-page, justified output)
cat > "$HTML_TEMP" <<EOF
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @page {
    margin: 0.60in; /* tuned for single-page */
  }
  body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10.4pt;
    line-height: 1.18;
    margin: 0;
    padding: 0;
  }
  div {
    white-space: pre-line;
    text-align: justify;
    text-justify: inter-word;
    margin-bottom: 4px;
  }
  div:empty { height: 8px; }
  a { color: #0645AD; text-decoration: underline; }
  strong { font-weight: 700; }
</style>
</head>
<body>
$DIV_CONTENT
</body>
</html>
EOF

###########################################
# Prince PDF Conversion
###########################################
if ! command -v prince >/dev/null 2>&1; then
  echo "ERROR: PrinceXML not installed. Install via: brew install prince"
  exit 1
fi

prince ${HTML_TEMP} -o ${PDF_OUTPUT} 2>/dev/null

echo "Generated PDF:" ${PDF_OUTPUT}

###########################################
# Cleanup
###########################################
rm -f ${TXT_OUTPUT} ${HTML_TEMP}

echo "✔ Done!"
