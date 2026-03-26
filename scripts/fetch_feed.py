#!/usr/bin/env python3
"""
AI Feed 자동 수집 스크립트
- GitHub 스타 100+ repos (Claude Code, MCP, 데이터 시각화 등)
- Claude Code 공식 docs changelog
- 2시간마다 실행 (GitHub Actions)
"""

import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "ai-feed-bot/1.0",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# 추적할 레포 목록 (직접 지정)
# twitterapi.io API Key
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "new1_84ea19ca7edd462b8c959031d075abb6")

WATCH_REPOS = [
    # Claude Code 관련
    "anthropics/claude-code",
    "anthropics/anthropic-cookbook",
    "anthropics/model-context-protocol",
    # Claude Code 커뮤니티 도구
    "danilofalcao/cursor-claude",
    "getmaxun/maxun",
    "harnessio/harness",
    "steipete/claude-code-hooks-mastery",
    "Aider-AI/aider",
    "cline/cline",
    "continuedev/continue",
    # MCP
    "modelcontextprotocol/servers",
    "wong2/awesome-mcp-servers",
    "punkpeye/awesome-mcp-servers",
    "MarkusPfundstein/mcp-obsidian",
    # 데이터 시각화 / 분석
    "uwdata/mosaic",
    "uwdata/vega-lite",
    "observablehq/framework",
    "apache/superset",
    "metabase/metabase",
    # 프롬프트 / AI 실무
    "dair-ai/Prompt-Engineering-Guide",
    "brexhq/prompt-engineering",
    "trigaten/Learn_Prompting",
    # 홈페이지 / 프론트
    "shadcn-ui/ui",
    "tailwindlabs/tailwindcss",
    # DataBridge 관련
    "seoyeon924/Script",
]

# 키워드 기반 GitHub 검색
SEARCH_QUERIES = [
    "claude-code stars:>100",
    "mcp server claude stars:>50",
    "claude code hooks stars:>30",
    "superpower claude stars:>50",
    "oh-my-claude stars:>30",
    "anthropic claude agent stars:>100",
    "data visualization dashboard claude stars:>30",
    "claude code tutorial stars:>20",
]

def gh_api(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return None

def get_repo_info(full_name):
    data = gh_api(f"https://api.github.com/repos/{full_name}")
    if not data or data.get("message"):
        return None
    return {
        "id": f"gh-{full_name.replace('/', '-')}",
        "type": "github_repo",
        "title": data.get("name", ""),
        "full_name": full_name,
        "description": data.get("description") or "",
        "url": data.get("html_url", ""),
        "stars": data.get("stargazers_count", 0),
        "topics": data.get("topics", []),
        "language": data.get("language") or "",
        "updated_at": data.get("pushed_at", ""),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "tag": auto_tag(full_name, data.get("topics", []), data.get("description") or ""),
        "status": "inbox",
    }

def search_repos(query):
    q = urllib.parse.quote(query)
    data = gh_api(f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=10")
    if not data:
        return []
    items = []
    for item in data.get("items", []):
        fn = item.get("full_name", "")
        if not fn:
            continue
        items.append({
            "id": f"gh-{fn.replace('/', '-')}",
            "type": "github_repo",
            "title": item.get("name", ""),
            "full_name": fn,
            "description": item.get("description") or "",
            "url": item.get("html_url", ""),
            "stars": item.get("stargazers_count", 0),
            "topics": item.get("topics", []),
            "language": item.get("language") or "",
            "updated_at": item.get("pushed_at", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "tag": auto_tag(fn, item.get("topics", []), item.get("description") or ""),
            "status": "inbox",
        })
    return items

def auto_tag(full_name, topics, desc):
    text = (full_name + " " + " ".join(topics) + " " + desc).lower()
    if any(k in text for k in ["claude-code", "claude code", "anthropic"]):
        return "Claude Code"
    if any(k in text for k in ["mcp", "model-context-protocol"]):
        return "MCP"
    if any(k in text for k in ["visualization", "dashboard", "chart", "d3", "vega"]):
        return "데이터 시각화"
    if any(k in text for k in ["prompt", "prompt-engineering"]):
        return "프롬프트"
    if any(k in text for k in ["nextjs", "react", "tailwind", "frontend"]):
        return "프론트엔드"
    return "기타"

def get_claude_changelog():
    """Claude Code 공식 changelog RSS/문서 확인"""
    try:
        req = urllib.request.Request(
            "https://code.claude.com/docs/en/changelog.md",
            headers={"User-Agent": "ai-feed-bot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read().decode("utf-8", errors="replace")
        # 첫 번째 버전 섹션 파싱
        lines = text.split("\n")
        entries = []
        current = None
        for line in lines[:80]:
            m = re.match(r"^## (.+)", line)
            if m:
                if current:
                    entries.append(current)
                current = {
                    "id": f"changelog-{m.group(1).replace(' ', '-')}",
                    "type": "changelog",
                    "title": f"Claude Code 업데이트 — {m.group(1)}",
                    "description": "",
                    "url": "https://code.claude.com/docs/en/changelog",
                    "tag": "Claude Code",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "status": "inbox",
                    "stars": 0,
                }
            elif current and line.strip() and not line.startswith("##"):
                if len(current["description"]) < 300:
                    current["description"] += line.strip() + " "
        if current:
            entries.append(current)
        return entries[:5]
    except Exception as e:
        print(f"  Changelog ERR: {e}")
        return []

def fetch_plain(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ai-feed-bot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return None


def get_hn_posts():
    """HN에서 claude code 관련 인기 포스트 수집"""
    import urllib.parse as _urlparse
    queries = ["claude code", "claude AI agent", "MCP model context protocol"]
    items = []
    seen = set()
    for q in queries:
        url = (
            f"https://hn.algolia.com/api/v1/search"
            f"?query={_urlparse.quote(q)}&tags=story&hitsPerPage=10"
            f"&numericFilters=points>10"
        )
        data = fetch_plain(url)
        if not data:
            continue
        for hit in data.get("hits", []):
            pts = hit.get("points", 0)
            if pts < 10:
                continue
            oid = hit.get("objectID", "")
            item_id = f"hn-{oid}"
            if item_id in seen:
                continue
            seen.add(item_id)
            item = {
                "id": item_id,
                "type": "hn",
                "platform": "HN",
                "author": hit.get("author", ""),
                "title": hit.get("title", ""),
                "description": hit.get("story_text", "") or "",
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                "hn_url": f"https://news.ycombinator.com/item?id={oid}",
                "score": pts,
                "comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", ""),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "tag": "Claude Code",
                "status": "inbox",
                "stars": pts,
            }
            items.append(item)
    return items


def get_reddit_posts():
    subreddits = ["ClaudeAI", "AIToolsHub", "artificial"]
    keywords = ["claude code", "mcp", "claude agent"]
    items = []
    seen = set()
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=20"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ai-feed-bot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"  Reddit ERR r/{sub}: {e}")
            continue
        for post in data.get("data", {}).get("children", []):
            p = post.get("data", {})
            title = p.get("title", "").lower()
            text = p.get("selftext", "").lower()
            if not any(k in title or k in text for k in keywords):
                continue
            ups = p.get("ups", 0)
            if ups < 10:
                continue
            item_id = f"reddit-{p.get('id', '')}"
            if item_id in seen:
                continue
            seen.add(item_id)
            item = {
                "id": item_id,
                "type": "reddit",
                "platform": "Reddit",
                "author": p.get("author", ""),
                "subreddit": sub,
                "title": p.get("title", ""),
                "description": (p.get("selftext", "") or "")[:500],
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "score": ups,
                "comments": p.get("num_comments", 0),
                "created_at": datetime.fromtimestamp(p.get("created_utc", 0), tz=timezone.utc).isoformat(),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "tag": "Claude Code",
                "status": "inbox",
                "stars": ups,
            }
            items.append(item)
    return items


def main():
    import urllib.parse

    print("=== AI Feed 수집 시작 ===")
    new_items = []
    seen_ids = set()

    # 1. 고정 레포 목록
    print("\n[1] 고정 레포 수집...")
    for repo in WATCH_REPOS:
        info = get_repo_info(repo)
        if info and info["id"] not in seen_ids and info["stars"] >= 20:
            new_items.append(info)
            seen_ids.add(info["id"])
            print(f"  ✓ {repo} ★{info['stars']}")

    # 2. 검색 기반 수집
    print("\n[2] 검색 기반 수집...")
    for query in SEARCH_QUERIES:
        results = search_repos(query)
        for item in results:
            if item["id"] not in seen_ids and item["stars"] >= 30:
                new_items.append(item)
                seen_ids.add(item["id"])
                print(f"  ✓ {item['full_name']} ★{item['stars']}")

    # 3. Claude Code 공식 changelog
    print("\n[3] Changelog 수집...")
    changelog = get_claude_changelog()
    for c in changelog:
        if c["id"] not in seen_ids:
            new_items.append(c)
            seen_ids.add(c["id"])
            print(f"  ✓ {c['title']}")

    # 4. HN 포스트 수집
    print("\n[4] HN 포스트 수집...")
    hn_posts = get_hn_posts()
    for item in hn_posts:
        if item["id"] not in seen_ids:
            new_items.append(item)
            seen_ids.add(item["id"])
            print(f"  ✓ [HN] {item['title'][:60]} ★{item['stars']}")

    # 5. Reddit 포스트 수집
    print("\n[5] Reddit 포스트 수집...")
    reddit_posts = get_reddit_posts()
    for item in reddit_posts:
        if item["id"] not in seen_ids:
            new_items.append(item)
            seen_ids.add(item["id"])
            print(f"  ✓ [Reddit r/{item['subreddit']}] {item['title'][:50]} ★{item['stars']}")

    # X(Twitter) 수집
    print("\n[4] X(Twitter) 수집...")
    if TWITTER_API_KEY:
        x_items = get_x_posts(TWITTER_API_KEY)
        for item in x_items:
            if item["id"] not in seen_ids:
                new_items.append(item)
                seen_ids.add(item["id"])
                print(f"  ✓ [X @{item['author']}] {item['title'][:50]} ❤{item['stars']}")
    
    # 기존 feed.json 로드 (status 보존)
    feed_path = "data/feed.json"
    existing = {}
    if os.path.exists(feed_path):
        with open(feed_path) as f:
            old = json.load(f)
        for item in old.get("items", []):
            existing[item["id"]] = item

    # 병합: 기존 status/chapter 보존, 새 항목 추가
    merged = []
    for item in new_items:
        if item["id"] in existing:
            old_item = existing[item["id"]]
            item["status"] = old_item.get("status", "inbox")
            item["chapter"] = old_item.get("chapter", "")
            item["note"] = old_item.get("note", "")
        merged.append(item)

    # 스코어 내림차순 정렬
    merged.sort(key=lambda x: x.get("stars", 0), reverse=True)

    feed = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(merged),
        "items": merged,
    }
    os.makedirs("data", exist_ok=True)
    with open(feed_path, "w") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print(f"\n=== 완료: {len(merged)}개 저장 ===")

if __name__ == "__main__":
    main()


def get_x_posts(api_key):
    """twitterapi.io로 X(Twitter) Claude Code 관련 포스트 수집"""
    import subprocess
    queries = [
        "claude code",
        "MCP model context protocol claude",
        "claude code hooks skills",
        "anthropic claude agent",
        "claude code tips workflow",
    ]
    items = []
    seen = set()
    for q in queries:
        result = subprocess.run([
            'curl', '-s',
            f"https://api.twitterapi.io/twitter/tweet/advanced_search?query={q.replace(' ','+')}&queryType=Top&count=8",
            '-H', f'X-API-Key: {api_key}',
            '-H', 'Accept: application/json',
        ], capture_output=True, text=True, timeout=30)
        try:
            data = json.loads(result.stdout)
            for t in data.get('tweets', []):
                tid = t.get('id', '')
                if not tid or tid in seen:
                    continue
                seen.add(tid)
                auth = t.get('author', {})
                likes = t.get('likeCount', 0)
                if likes < 5:
                    continue
                item = {
                    'id': f"x-{tid}",
                    'type': 'x',
                    'platform': 'X',
                    'author': auth.get('userName', ''),
                    'author_name': auth.get('name', ''),
                    'title': t.get('text', '')[:120],
                    'description': t.get('text', ''),
                    'url': t.get('url') or f"https://x.com/{auth.get('userName','')}/status/{tid}",
                    'score': likes,
                    'comments': t.get('replyCount', 0),
                    'created_at': t.get('createdAt', ''),
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'tag': 'Claude Code',
                    'status': 'inbox',
                    'stars': likes,
                }
                items.append(item)
        except Exception as e:
            print(f"  X parse ERR: {e}")
    return items
