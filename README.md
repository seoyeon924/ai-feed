# AI Feed

DataBridge 패캠 스크립트 작성을 위한 AI/Claude Code 리소스 피드.

## 구조
- `index.html` — 피드 웹 UI (GitHub Pages)
- `data/feed.json` — 수집된 항목 데이터
- `scripts/fetch_feed.py` — 자동 수집 스크립트
- `.github/workflows/fetch-feed.yml` — 2시간마다 자동 실행

## 기능
- GitHub 스타 100+ repos 자동 수집 (Claude Code, MCP, 데이터 시각화 등)
- URL 직접 추가
- 카드 클릭 → 챕터 선택 → 승인 → Script repo 반영
