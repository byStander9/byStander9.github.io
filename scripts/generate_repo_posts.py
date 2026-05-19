#!/usr/bin/env python3
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "_data" / "repositories.json"
GENERATED_DATA_PATH = ROOT / "_data" / "repositories_generated.json"
AI_CACHE_PATH = ROOT / "_data" / "ai_enrichment_cache.json"
POSTS_DIR = ROOT / "_posts"

TEXT_EXTENSIONS = {
    ".c", ".cc", ".cfg", ".conf", ".cpp", ".cs", ".css", ".go", ".gradle",
    ".html", ".java", ".js", ".json", ".jsx", ".kt", ".md", ".mjs", ".php",
    ".properties", ".py", ".rb", ".rs", ".scss", ".sh", ".sql", ".ts", ".tsx",
    ".txt", ".xml", ".yaml", ".yml"
}

IMPORTANT_NAMES = {
    "README.md", "readme.md", "Readme.md", "package.json", "requirements.txt",
    "pyproject.toml", "Gemfile", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "pom.xml", "build.gradle", "settings.gradle",
    "Makefile", "app.py", "main.py", "bot.py", "index.js", "server.js"
}


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


CONFIG = load_config()
OWNER = CONFIG["owner"]
def github_token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token

    try:
        return subprocess.check_output(
            ["gh", "auth", "token"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
    except Exception:
        return ""


TOKEN = github_token()
EXCLUDED = set(CONFIG.get("excluded_repositories", []))
HIDDEN = set(CONFIG.get("hidden_repositories", []))
FEATURED = set(CONFIG.get("featured_repositories", []))
KEEP_MANUAL_POSTS = CONFIG.get("keep_manual_posts", True)
INCLUDE_FORKS = CONFIG.get("include_forks", False)
INCLUDE_ARCHIVED = CONFIG.get("include_archived", False)
AI_CONFIG = CONFIG.get("ai_enrichment", {})
AI_ENABLED = AI_CONFIG.get("enabled", False)
AI_PROVIDER = os.environ.get("AI_PROVIDER") or AI_CONFIG.get("provider", "openai_api")
AI_MODEL = os.environ.get("OPENAI_MODEL") or AI_CONFIG.get("model", "gpt-5.4-mini")
AI_REASONING_EFFORT = AI_CONFIG.get("reasoning_effort", "low")
AI_MAX_REPOSITORIES = int(AI_CONFIG.get("max_repositories_per_run", 6))
AI_MAX_INPUT_CHARS = int(AI_CONFIG.get("max_input_chars", 24000))
AI_PROMPT_VERSION = "2026-05-19"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
README_DRAFT_DIR = ROOT / AI_CONFIG.get("readme_draft_dir", "repo-readmes")


def github_get(path):
    request = Request(f"https://api.github.com{path}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404:
            return None
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API failed {exc.code}: {path}\n{body}") from exc


def openai_post(payload):
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Authorization", f"Bearer {OPENAI_API_KEY}")
    request.add_header("Content-Type", "application/json")

    with urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def response_text(payload):
    if payload.get("output_text"):
        return payload["output_text"]

    parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def command_exists(name):
    try:
        subprocess.check_output(
            ["where" if os.name == "nt" else "command", name],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
            shell=(os.name != "nt"),
        )
        return True
    except Exception:
        return False


def extract_json_object(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return json.loads(text[start : end + 1])


def all_repositories():
    repos = []
    page = 1
    while True:
        batch = github_get(f"/users/{OWNER}/repos?type=owner&sort=updated&per_page=100&page={page}")
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def is_excluded(repo):
    return repo["name"] in EXCLUDED or repo["full_name"] in EXCLUDED


def is_hidden(repo):
    return repo["name"] in HIDDEN or repo["full_name"] in HIDDEN


def status_for(repo):
    if is_excluded(repo):
        return "excluded"
    if is_hidden(repo):
        return "hidden"
    if repo["name"] in FEATURED or repo["full_name"] in FEATURED:
        return "featured"
    return "published"


def slugify(value):
    slug = re.sub(r"[^a-z0-9가-힣]+", "-", value.lower()).strip("-")
    return slug or "repo"


def yaml_escape(value):
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"')


def array_yaml(values):
    unique = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return ", ".join(f'"{yaml_escape(value)}"' for value in unique)


def manual_posts_by_repo():
    result = {}
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) < 3:
            continue
        front_matter = parts[1]
        repo_name = ""
        generated = False

        match = re.search(r"^repo:\s*[\"']?([^\"'\n]+)[\"']?\s*$", front_matter, re.MULTILINE)
        if match:
            repo_name = match.group(1).strip()

        if not repo_name:
            match = re.search(rf"github\.com/{re.escape(OWNER)}/([^/\"'\s]+)", front_matter)
            if match:
                repo_name = match.group(1).strip()

        generated = bool(re.search(r"^generated:\s*true\s*$", front_matter, re.MULTILINE))

        if repo_name:
            result[repo_name] = {"path": path, "generated": generated}
    return result


def root_contents(repo):
    try:
        return github_get(f"/repos/{repo['full_name']}/contents?ref={quote(repo['default_branch'])}") or []
    except Exception as exc:
        print(f"Skipping root contents for {repo['full_name']}: {exc}", file=sys.stderr)
        return []


def tree_contents(repo):
    try:
        tree = github_get(f"/repos/{repo['full_name']}/git/trees/{quote(repo['default_branch'])}?recursive=1")
        return [item for item in (tree or {}).get("tree", []) if item.get("type") == "blob"]
    except Exception as exc:
        print(f"Skipping tree for {repo['full_name']}: {exc}", file=sys.stderr)
        return []


def fetch_content(repo, path):
    encoded = "/".join(quote(part) for part in path.split("/"))
    try:
        payload = github_get(f"/repos/{repo['full_name']}/contents/{encoded}?ref={quote(repo['default_branch'])}")
        if not payload or not payload.get("content"):
            return ""
        return base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"Skipping file {repo['full_name']}/{path}: {exc}", file=sys.stderr)
        return ""


def readme_text(repo, root_files):
    readme = next(
        (
            item for item in root_files
            if item.get("type") == "file" and item.get("name", "").lower().startswith("readme")
        ),
        None,
    )
    return fetch_content(repo, readme["path"]) if readme else ""


def important_files(repo, tree):
    candidates = []
    for item in tree:
        path = item["path"]
        name = Path(path).name
        ext = Path(path).suffix
        if name in IMPORTANT_NAMES or ext in TEXT_EXTENSIONS:
            if int(item.get("size", 0)) <= 40_000:
                candidates.append(item)

    candidates.sort(key=lambda item: (item["path"].count("/"), item["path"]))
    return {item["path"]: fetch_content(repo, item["path"]) for item in candidates[:8]}


def load_ai_cache():
    if not AI_CACHE_PATH.exists():
        return {}
    return json.loads(AI_CACHE_PATH.read_text(encoding="utf-8"))


def write_ai_cache(cache):
    AI_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ai_cache_key(repo):
    return repo["full_name"]


def readme_draft_path(repo):
    return README_DRAFT_DIR / f"{slugify(repo['name'])}.md"


def truncate(value, limit):
    value = value or ""
    if len(value) <= limit:
        return value
    return value[:limit] + "\n\n[truncated]"


def repo_context(repo, readme, tree, files):
    file_lines = []
    budget = AI_MAX_INPUT_CHARS

    for path, text in files.items():
        excerpt_limit = min(3000, max(800, budget // max(len(files), 1)))
        excerpt = truncate(text, excerpt_limit)
        budget -= len(excerpt)
        file_lines.append(f"### {path}\n```text\n{excerpt}\n```")

    file_list = "\n".join(f"- {item['path']}" for item in tree[:80])
    return truncate(
        f"""
Repository:
- name: {repo['name']}
- full_name: {repo['full_name']}
- url: {repo['html_url']}
- description: {repo.get('description') or ''}
- language: {repo.get('language') or ''}
- default_branch: {repo.get('default_branch') or ''}
- pushed_at: {repo.get('pushed_at') or ''}

README:
```markdown
{truncate(readme, 8000)}
```

Files:
{file_list}

Important file excerpts:
{chr(10).join(file_lines)}
""".strip(),
        AI_MAX_INPUT_CHARS,
    )


def enrichment_prompt(repo, readme, tree, files):
    return (
        "레포 정보를 바탕으로 1) README 초안 2) GitHub Pages 블로그 포스트 본문을 작성해줘. "
        "README는 프로젝트 소개, 주요 기능, 구조, 실행/사용 방법, 보강하면 좋은 점을 포함해. "
        "블로그 포스트는 개발 경험 정리 느낌으로 쓰고, 과장하지 말아줘. "
        "반드시 JSON 객체 하나만 출력해. 키는 summary, categories, tags, readme_markdown, "
        "post_markdown_body만 사용해.\n\n"
        f"{repo_context(repo, readme, tree, files)}"
    )


def ai_enrich_repo(repo, readme, tree, files):
    if not AI_ENABLED:
        return None

    if AI_PROVIDER == "codex_cli":
        return ai_enrich_repo_with_codex(repo, readme, tree, files)

    if AI_PROVIDER == "openai_api":
        return ai_enrich_repo_with_openai_api(repo, readme, tree, files)

    print(f"Unknown AI provider '{AI_PROVIDER}'. Falling back to rule-based generation.", file=sys.stderr)
    return None


def ai_enrich_repo_with_openai_api(repo, readme, tree, files):
    if not OPENAI_API_KEY:
        return None

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "categories": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}},
            "readme_markdown": {"type": "string"},
            "post_markdown_body": {"type": "string"},
        },
        "required": ["summary", "categories", "tags", "readme_markdown", "post_markdown_body"],
    }
    payload = {
        "model": AI_MODEL,
        "instructions": (
            "You write Korean developer portfolio content. Use only the repository context. "
            "Do not invent unverified features. If the repository is sparse, say what can be inferred. "
            "Return polished Markdown. Keep README practical and the blog post reflective."
        ),
        "input": enrichment_prompt(repo, readme, tree, files),
        "max_output_tokens": 5000,
        "reasoning": {"effort": AI_REASONING_EFFORT},
        "text": {
            "format": {
                "type": "json_schema",
                "name": "repo_blog_enrichment",
                "strict": True,
                "schema": schema,
            }
        },
    }

    try:
        result = openai_post(payload)
        content = response_text(result)
        return json.loads(content)
    except Exception as exc:
        print(f"Skipping AI enrichment for {repo['full_name']}: {exc}", file=sys.stderr)
        return None


def ai_enrich_repo_with_codex(repo, readme, tree, files):
    if not command_exists("codex"):
        return None

    prompt = (
        "You write Korean developer portfolio content. Use only the repository context. "
        "Do not modify files or run commands. Return one valid JSON object only. "
        "Do not wrap it in Markdown fences.\n\n"
        f"{enrichment_prompt(repo, readme, tree, files)}"
    )
    command = [
        "codex",
        "exec",
        "--model",
        AI_MODEL,
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        "--cd",
        str(ROOT),
        prompt,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=420,
            check=True,
        )
        return extract_json_object(completed.stdout)
    except Exception as exc:
        print(f"Skipping Codex enrichment for {repo['full_name']}: {exc}", file=sys.stderr)
        return None


def readme_summary(readme):
    lines = [line.strip() for line in readme.splitlines() if line.strip()]
    useful = [
        line for line in lines
        if not line.startswith(("!", "[!", "<img", "---")) and len(line) >= 8
    ]
    headings = [re.sub(r"^#+\s*", "", line) for line in useful if line.startswith("#")][:5]
    bullets = [re.sub(r"^[-*]\s+", "", line) for line in useful if re.match(r"^[-*]\s+", line)][:6]
    prose = [
        line for line in useful
        if not line.startswith("#") and not re.match(r"^[-*]\s+", line) and not line.startswith("```")
    ][:4]
    return {"headings": headings, "bullets": bullets, "prose": prose}


def top_level_tree(tree):
    root_files = [item["path"] for item in tree if item["path"].count("/") == 0][:12]
    dirs = []
    for item in tree:
        first = item["path"].split("/")[0]
        if first not in root_files and first not in dirs:
            dirs.append(first)
    return {"files": root_files, "dirs": dirs[:12]}


def detect_stack(repo, files):
    stack = []
    if repo.get("language"):
        stack.append(repo["language"])
    if {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"} & set(files):
        stack.append("Docker")
    if "requirements.txt" in files or "pyproject.toml" in files or any(path.endswith(".py") for path in files):
        stack.append("Python")
    if "package.json" in files:
        stack.append("Node.js")
    if "pom.xml" in files or "build.gradle" in files or any(path.endswith(".java") for path in files):
        stack.append("Java")
    if "Gemfile" in files and any("jekyll" in text for text in files.values()):
        stack.append("Jekyll")

    package = files.get("package.json", "")
    package_checks = {
        "React": "react",
        "Next.js": "next",
        "Vite": "vite",
        "Express": "express",
    }
    for label, needle in package_checks.items():
        if needle in package:
            stack.append(label)

    unique = []
    for item in stack:
        if item and item not in unique:
            unique.append(item)
    return unique


def file_hint(path):
    name = Path(path).name
    if name.lower().startswith("readme"):
        return "프로젝트 소개와 사용법을 담은 문서"
    if name in {"requirements.txt", "pyproject.toml", "package.json", "pom.xml", "build.gradle", "Gemfile"}:
        return "의존성과 실행 환경을 추정할 수 있는 설정 파일"
    if name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
        return "컨테이너 실행 또는 배포 구성을 담은 파일"
    return "구현 흐름을 확인할 수 있는 코드/설정 파일"


def description_or_summary(repo, summary_data):
    description = (repo.get("description") or "").strip()
    if description:
        return description
    if summary_data["prose"]:
        return summary_data["prose"][0]
    return f"{repo['name']} 레포의 README와 파일 구조를 기준으로 정리한 개발 기록."


def categories_for(repo, stack, ai_content=None):
    if ai_content and ai_content.get("categories"):
        values = ["repository"] + [slugify(str(value)) for value in ai_content["categories"]]
        return [value for value in values if value][:4]

    values = ["repository"]
    if repo.get("language"):
        values.append(repo["language"].lower())
    values.extend(item.lower() for item in stack[:2])
    unique = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return unique[:4]


def tags_for(repo, stack, ai_content=None):
    if ai_content and ai_content.get("tags"):
        values = list(ai_content["tags"]) + [repo["name"]]
        unique = []
        for value in values:
            tag = slugify(str(value))
            if tag and tag not in unique:
                unique.append(tag)
        return unique[:8]

    values = list(repo.get("topics") or []) + stack + [repo["name"]]
    unique = []
    for value in values:
        tag = slugify(str(value))
        if tag and tag not in unique:
            unique.append(tag)
    return unique[:8]


def parse_github_time(value):
    if not value:
        return dt.datetime.now(dt.timezone.utc)
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def generated_post_path(repo, post_date):
    return POSTS_DIR / f"{post_date:%Y-%m-%d}-{slugify(repo['name'])}-repo-notes.md"


def render_rule_based_body(repo, readme, tree, files, stack):
    summary_data = readme_summary(readme)
    summary = description_or_summary(repo, summary_data)
    post_date = parse_github_time(repo.get("pushed_at") or repo.get("updated_at")).astimezone(
        dt.timezone(dt.timedelta(hours=9))
    )
    top_level = top_level_tree(tree)
    important_paths = list(files)[:6]
    body = []
    body.append(f"{repo['name']} 레포를 기준으로 README와 파일 구조를 자동으로 확인해 정리한 개발 기록이다.")
    body.append("이 글은 레포가 업데이트되면 GitHub Actions를 통해 다시 생성될 수 있다.")
    body.append("")
    body.append("## 레포 개요")
    body.append("")
    body.append(f"- 레포 주소: <{repo['html_url']}>")
    body.append(f"- 기본 브랜치: `{repo['default_branch']}`")
    body.append(f"- 주요 언어: {repo.get('language') or '미지정'}")
    body.append(f"- 최근 업데이트: {post_date:%Y.%m.%d}")
    body.append(f"- 설명: {summary}")
    body.append("")
    body.append("## README에서 확인한 내용")
    body.append("")

    if not readme.strip():
        body.append("현재 README를 찾지 못했다. 나중에 설치 방법, 실행 방법, 핵심 기능을 README에 추가하면 이 글도 더 풍부해진다.")
    else:
        if summary_data["headings"]:
            body.append("README의 주요 섹션은 다음과 같다.")
            body.append("")
            body.extend(f"- {heading}" for heading in summary_data["headings"])
            body.append("")
        lines = list(dict.fromkeys(summary_data["prose"] + summary_data["bullets"]))[:8]
        if lines:
            body.append("README에서 눈에 띄는 내용은 다음과 같다.")
            body.append("")
            body.extend(f"- {re.sub(r'\\s+', ' ', line)}" for line in lines)
        else:
            body.append("README는 존재하지만 자동 요약에 활용할 만한 문장이 많지 않았다.")

    body.append("")
    body.append("## 파일 구조 메모")
    body.append("")
    if not tree:
        body.append("파일 트리를 가져오지 못했다. 레포 접근 권한이나 기본 브랜치 상태를 확인하면 좋다.")
    else:
        body.append("최상위에서 확인되는 주요 항목은 다음과 같다.")
        body.append("")
        body.append("```text")
        body.extend(f"{directory}/" for directory in top_level["dirs"])
        body.extend(top_level["files"])
        body.append("```")

    body.append("")
    body.append("## 기술 스택 단서")
    body.append("")
    if stack:
        body.append("레포 메타데이터와 설정 파일 기준으로는 다음 기술이 보인다.")
        body.append("")
        body.extend(f"- {item}" for item in stack)
    else:
        body.append("언어와 의존성 파일 기준으로 뚜렷한 기술 스택을 판단하기는 어려웠다.")

    body.append("")
    body.append("## 우선 확인할 파일")
    body.append("")
    if important_paths:
        body.extend(f"- `{path}`: {file_hint(path)}" for path in important_paths)
    else:
        body.append("자동으로 읽을 만한 텍스트 파일을 충분히 찾지 못했다.")

    body.append("")
    body.append("## 다시 볼 때의 체크포인트")
    body.append("")
    body.append("1. README에 실행 방법과 필요한 환경 변수가 충분히 적혀 있는지 확인한다.")
    body.append("2. 핵심 코드가 어떤 파일에 모여 있는지 보고, 기능이 커졌다면 분리 기준을 정한다.")
    body.append("3. 의존성 파일을 기준으로 로컬 실행과 배포 흐름이 재현 가능한지 확인한다.")
    body.append("4. 블로그에 보여주고 싶지 않은 레포라면 `_data/repositories.json`의 `hidden_repositories`로 옮긴다.")

    return "\n".join(body) + "\n"


def render_post(repo, readme, tree, files, ai_content=None):
    summary_data = readme_summary(readme)
    stack = detect_stack(repo, files)
    summary = (ai_content or {}).get("summary") or description_or_summary(repo, summary_data)
    post_date = parse_github_time(repo.get("pushed_at") or repo.get("updated_at")).astimezone(
        dt.timezone(dt.timedelta(hours=9))
    )
    draft_relative_path = ""
    if ai_content and ai_content.get("readme_markdown"):
        draft_relative_path = readme_draft_path(repo).relative_to(ROOT).as_posix()

    front_matter = f"""---
layout: post
title: "{yaml_escape(repo['name'])} 개발 기록"
date: {post_date:%Y-%m-%d %H:%M:%S %z}
categories: [{array_yaml(categories_for(repo, stack, ai_content))}]
tags: [{array_yaml(tags_for(repo, stack, ai_content))}]
summary: "{yaml_escape(summary)}"
repo: "{yaml_escape(repo['name'])}"
repo_url: "{repo['html_url']}"
generated: true
ai_enriched: {str(bool(ai_content)).lower()}
"""
    if draft_relative_path:
        front_matter += f'readme_draft_url: "/{draft_relative_path}"\n'
    front_matter += "---\n\n"

    if ai_content and ai_content.get("post_markdown_body"):
        body = ai_content["post_markdown_body"].strip() + "\n"
    else:
        body = render_rule_based_body(repo, readme, tree, files, stack)

    return front_matter + body


def write_generated_data(repos):
    data = []
    for repo in repos:
        data.append(
            {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "url": repo["html_url"],
                "description": repo.get("description"),
                "language": repo.get("language"),
                "topics": repo.get("topics") or [],
                "status": status_for(repo),
                "pushed_at": repo.get("pushed_at"),
                "updated_at": repo.get("updated_at"),
            }
        )
    GENERATED_DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def remove_stale_generated_posts(active_repo_names):
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
        if len(parts) < 3:
            continue
        front_matter = parts[1]
        if not re.search(r"^generated:\s*true\s*$", front_matter, re.MULTILINE):
            continue
        match = re.search(r"^repo:\s*[\"']?([^\"'\n]+)[\"']?\s*$", front_matter, re.MULTILINE)
        repo_name = match.group(1).strip() if match else ""
        if repo_name not in active_repo_names:
            path.unlink()


def main():
    POSTS_DIR.mkdir(exist_ok=True)
    GENERATED_DATA_PATH.parent.mkdir(exist_ok=True)
    README_DRAFT_DIR.mkdir(exist_ok=True)

    repositories = all_repositories()
    repositories = [repo for repo in repositories if INCLUDE_FORKS or not repo.get("fork")]
    repositories = [repo for repo in repositories if INCLUDE_ARCHIVED or not repo.get("archived")]
    repositories.sort(key=lambda repo: repo.get("pushed_at") or repo.get("updated_at") or "", reverse=True)

    write_generated_data([repo for repo in repositories if not is_excluded(repo)])

    manual_posts = manual_posts_by_repo()
    active_generated = set()
    ai_cache = load_ai_cache()
    ai_used = 0

    for repo in repositories:
        if status_for(repo) in {"excluded", "hidden"}:
            continue

        existing = manual_posts.get(repo["name"])
        if existing and KEEP_MANUAL_POSTS and not existing["generated"]:
            print(f"Keeping manual post for {repo['name']}: {existing['path']}", file=sys.stderr)
            continue

        root_files = root_contents(repo)
        tree = tree_contents(repo)
        readme = readme_text(repo, root_files)
        files = important_files(repo, tree)
        ai_content = None
        key = ai_cache_key(repo)
        cache_entry = ai_cache.get(key, {})
        draft_path = readme_draft_path(repo)
        is_cached = (
            cache_entry.get("pushed_at") == repo.get("pushed_at")
            and cache_entry.get("model") == AI_MODEL
            and cache_entry.get("provider") == AI_PROVIDER
            and cache_entry.get("prompt_version") == AI_PROMPT_VERSION
            and draft_path.exists()
        )
        if AI_ENABLED and OPENAI_API_KEY and not is_cached and ai_used < AI_MAX_REPOSITORIES:
            ai_content = ai_enrich_repo(repo, readme, tree, files)
            if ai_content:
                draft_path.write_text(ai_content["readme_markdown"].strip() + "\n", encoding="utf-8")
                ai_cache[key] = {
                    "pushed_at": repo.get("pushed_at"),
                    "provider": AI_PROVIDER,
                    "model": AI_MODEL,
                    "prompt_version": AI_PROMPT_VERSION,
                    "readme_draft": draft_path.relative_to(ROOT).as_posix(),
                    "content": ai_content,
                    "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
                ai_used += 1
        elif is_cached and draft_path.exists():
            ai_content = cache_entry.get("content")
            if ai_content:
                ai_content["readme_markdown"] = draft_path.read_text(encoding="utf-8")

        post_date = parse_github_time(repo.get("pushed_at") or repo.get("updated_at")).astimezone(
            dt.timezone(dt.timedelta(hours=9))
        )
        path = existing["path"] if existing and existing["generated"] else generated_post_path(repo, post_date)

        path.write_text(render_post(repo, readme, tree, files, ai_content), encoding="utf-8")
        active_generated.add(repo["name"])

    remove_stale_generated_posts(active_generated)
    write_ai_cache(ai_cache)

    print(f"Repository inventory: {len(repositories)}")
    print(f"Generated/updated posts: {len(active_generated)}")
    print(f"AI enrichments used: {ai_used}")


if __name__ == "__main__":
    main()
