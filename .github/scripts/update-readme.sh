#!/usr/bin/env bash
# Refresh the auto-generated README sections between <!-- START:x --> / <!-- END:x --> markers.
# Needs: gh (authenticated via GH_TOKEN), jq, python3.
set -euo pipefail

USER="mynk03"
README="README.md"
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Repos never listed under "Recent Repositories" (old profile repo, tutorials, practice apps)
EXCLUDE="mayank4code DiceGame DrumKit Guess-The-Number Simon-Game To-Do-List keeper-app-1 Weather-React-App rechart_reactjs Blog-Website Todos_web"

# --- Projects: top 6 non-fork, non-excluded public repos sorted by pushed_at ---
gh api "users/$USER/repos?per_page=100&sort=pushed&type=owner" \
  | jq -r --arg user "$USER" --arg exclude "$EXCLUDE" '
      ($exclude | split(" ")) as $ex
      | [.[] | select(.fork == false and .private == false and .name != $user
                      and (.name as $n | $ex | index($n) | not))][:6]
      | .[] | "\(.full_name)|\(.html_url)|\((.description // "—") | gsub("\\|"; "\\|"))"' \
  > "$TMPDIR/repos_meta"

# Stack via /languages: prefer backend / typed languages, drop markup and tooling.
PRIORITY="Go Solidity TypeScript JavaScript Java C++ C Python Rust"
SKIP_LANGS="HTML CSS SCSS EJS Shell Dockerfile Makefile Procfile MDX Nix HCL Roff Batchfile PowerShell"

resolve_stack() {
  local repo=$1
  gh api "repos/$repo/languages" 2>/dev/null \
    | jq -r --arg priority "$PRIORITY" --arg skip "$SKIP_LANGS" '
        ($skip | split(" ")) as $skip_arr
        | ($priority | split(" ")) as $prio_arr
        | to_entries
        | map(select(.key as $k | $skip_arr | index($k) | not))
        | . as $langs
        | ([$prio_arr[] as $p | $langs[] | select(.key == $p) | .key]
            + ($langs | sort_by(-.value) | map(.key)))
        | reduce .[] as $k ([]; if any(.[]; . == $k) then . else . + [$k] end)
        | .[0:2]
        | join(", ")
      '
}

{
  echo "| Repository | Description | Stack |"
  echo "| --- | --- | --- |"
  while IFS='|' read -r repo url desc; do
    stack=$(resolve_stack "$repo")
    [ -z "$stack" ] && stack="—"
    echo "| [${repo#*/}]($url) | $desc | $stack |"
  done < "$TMPDIR/repos_meta"
} > "$TMPDIR/projects.md"

# --- Open source: PRs to other people's repos, grouped by repo in one collapsed card ---
gh search prs --author="$USER" --limit=1000 --json repository,title,url,state -- "-user:$USER" \
  | jq -r --arg user "$USER" '
      [.[] | select(.repository.nameWithOwner | startswith($user + "/") | not)]
      | group_by(.repository.nameWithOwner)
      | map({
          repo: .[0].repository.nameWithOwner,
          count: length,
          prs: [.[] | {num: (.url | split("/") | .[-1]), url: .url, title: .title}]
        })
      | sort_by(-.count)
      | . as $groups
      | ($groups | map(.count) | add // 0) as $total
      | if ($groups | length) == 0 then "" else
          "<details>\n"
          + "<summary><b>" + ($total | tostring) + " PR" + (if $total > 1 then "s" else "" end)
          + " across " + ($groups | length | tostring) + " repo" + (if ($groups | length) > 1 then "s" else "" end) + "</b>"
          + " &nbsp;<sub><i>(click to expand)</i></sub></summary>\n\n"
          + ($groups | map(
              "<details>\n"
              + "<summary><b><a href=\"https://github.com/" + .repo + "\">" + (.repo | gsub("/"; " / ")) + "</a></b> &middot; "
              + (.count | tostring) + " PR" + (if .count > 1 then "s" else "" end)
              + " &middot; <a href=\"https://github.com/" + .repo + "/pulls?q=author%3A" + $user + "+is%3Apr\">view all →</a>"
              + "</summary>\n\n"
              + (.prs | map("- [`#" + .num + "`](" + .url + ") — " + .title) | join("\n"))
              + "\n\n</details>"
            ) | join("\n\n"))
          + "\n\n</details>"
        end' > "$TMPDIR/ecosystem.md"

[ -s "$TMPDIR/ecosystem.md" ] || echo "_No external PRs yet._" > "$TMPDIR/ecosystem.md"

# --- Splice into README between markers ---
python3 - "$README" "$TMPDIR" <<'PY'
import re, sys, pathlib
readme_path, tmpdir = sys.argv[1], sys.argv[2]
data = pathlib.Path(readme_path).read_text()

for marker in ("projects", "ecosystem"):
    content = pathlib.Path(f"{tmpdir}/{marker}.md").read_text().rstrip()
    pat = re.compile(rf"(<!-- START:{marker} -->).*?(<!-- END:{marker} -->)", re.DOTALL)
    data = pat.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(2)}", data)

pathlib.Path(readme_path).write_text(data)
print(f"README updated: {readme_path}")
PY
