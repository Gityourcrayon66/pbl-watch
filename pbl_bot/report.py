"""SQLite → HTML 일일 리포트 생성.

생성 결과:
  docs/index.html       — 최신 N건 (GitHub Pages 메인)
  docs/YYYY-MM-DD.html  — 그날 신규 (이메일 본문으로도 사용)
"""
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .storage import Storage

DOCS_DIR = config.PROJECT_ROOT / "docs"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
INDEX_MAX = 100

CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans KR",sans-serif;
  margin:0;padding:24px;background:#fafafa;color:#111;line-height:1.5;max-width:900px;margin:0 auto}
h1{margin:0 0 4px}
.sub{color:#666;font-size:14px;margin-bottom:24px}
.card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:16px;margin-bottom:12px}
.src{display:inline-block;background:#eef;color:#225;font-size:12px;padding:2px 8px;border-radius:4px;margin-right:6px}
.title{font-weight:600;margin:6px 0}
.lead{color:#222;background:#f5f7fa;border-left:3px solid #4a90e2;padding:8px 12px;margin:8px 0;font-size:14px}
.points{margin:8px 0;padding-left:20px;font-size:14px}
.meta{font-size:13px;color:#666;margin-top:8px}
.rel-high{color:#0a8}
.rel-medium{color:#a80}
.rel-low,.rel-unknown{color:#888}
a{color:#225;text-decoration:none}
a:hover{text-decoration:underline}
.kw{display:inline-block;background:#f0f0f0;color:#555;font-size:11px;padding:1px 6px;border-radius:3px;margin-right:3px}
.empty{color:#888;padding:32px;text-align:center;background:#fff;border-radius:8px}
"""


def _card(doc: dict) -> str:
    try:
        s = json.loads(doc.get("summary_json") or "{}")
    except Exception:
        s = {}
    rel = s.get("PBL관련성") or "unknown"
    parts = [
        f'<span class="src">{html.escape(doc["source"])}</span>',
        f'<span class="rel-{html.escape(rel)}">관련성: {html.escape(rel)}</span>',
    ]
    title = doc.get("title") or "(제목 없음)"
    out = ['<div class="card">']
    out.append(f'<div>{ "".join(parts) }</div>')
    out.append(f'<div class="title">{html.escape(title)}</div>')
    if s.get("한줄요약"):
        out.append(f'<div class="lead">{html.escape(s["한줄요약"])}</div>')
    pts = s.get("핵심포인트") or []
    if pts:
        out.append("<ul class='points'>")
        for p in pts:
            out.append(f"<li>{html.escape(str(p))}</li>")
        out.append("</ul>")
    if s.get("관련성근거"):
        out.append(f'<div class="meta">{html.escape(s["관련성근거"])}</div>')
    kws = s.get("주요키워드") or []
    if kws:
        kw_html = " ".join(f'<span class="kw">{html.escape(str(k))}</span>' for k in kws)
        out.append(f'<div class="meta">{kw_html}</div>')
    out.append(f'<div class="meta"><a href="{html.escape(doc["url"])}" target="_blank">원문 →</a></div>')
    out.append("</div>")
    return "\n".join(out)


def _page(title: str, subtitle: str, docs: list[dict]) -> str:
    if not docs:
        body = '<div class="empty">표시할 자료가 없습니다.</div>'
    else:
        body = "\n".join(_card(d) for d in docs)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style></head>
<body>
<h1>{html.escape(title)}</h1>
<div class="sub">{html.escape(subtitle)}</div>
{body}
</body></html>
"""


def render() -> tuple[Path, Path | None]:
    DOCS_DIR.mkdir(exist_ok=True)
    store = Storage(config.DB_PATH)
    blocked = set(config.BLOCKED_URLS)
    docs = [d for d in store.all_summarized() if d["url"] not in blocked]

    # index.html: 최신 N건
    index_path = DOCS_DIR / "index.html"
    index_path.write_text(
        _page("PBL Watch", f"최신 {min(INDEX_MAX, len(docs))}건 · 생성 {TODAY} UTC", docs[:INDEX_MAX]),
        encoding="utf-8",
    )

    # YYYY-MM-DD.html: 오늘 신규 (요약 완료 시각 기준)
    today_docs = [d for d in docs if (d.get("summarized_at") or "").startswith(TODAY)]
    today_path = None
    if today_docs:
        today_path = DOCS_DIR / f"{TODAY}.html"
        today_path.write_text(
            _page(f"PBL Watch — {TODAY}", f"오늘 신규 {len(today_docs)}건", today_docs),
            encoding="utf-8",
        )

    return index_path, today_path


if __name__ == "__main__":
    idx, today = render()
    print(f"wrote: {idx}")
    if today:
        print(f"wrote: {today}")
    else:
        print("no new docs today, daily file skipped")
