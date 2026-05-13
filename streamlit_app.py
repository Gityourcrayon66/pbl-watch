import json
import sqlite3
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "pbl.db"
GITHUB_EDIT_URL = "https://github.com/Gityourcrayon66/pbl-watch/edit/main/pbl_bot/config.py"

sys.path.insert(0, str(ROOT))
from pbl_bot import config  # noqa: E402

BLOCKED = set(config.BLOCKED_URLS)

st.set_page_config(page_title="PBL Watch", layout="wide")
st.title("PBL Watch — Performance Based Logistics 자료 모음")

if not DB_PATH.exists():
    st.info("아직 데이터가 없습니다. `python -m pbl_bot.daily_run` 으로 첫 수집을 돌리거나, GitHub Actions가 매일 KST 07:00 자동 실행합니다.")
    st.stop()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
docs = [
    dict(r)
    for r in conn.execute(
        "SELECT * FROM documents WHERE status='summarized' ORDER BY summarized_at DESC"
    ).fetchall()
]
conn.close()

# BLOCKED 필터링 (DB는 안 건드림)
all_count = len(docs)
docs = [d for d in docs if d["url"] not in BLOCKED]

if not docs:
    st.info("수집된 문서는 있지만 표시할 게 없습니다.")
    st.stop()

with st.sidebar:
    st.subheader("필터")
    sources = sorted({d["source"] for d in docs})
    pick = st.multiselect("소스", sources, default=sources)
    query = st.text_input("키워드 검색")
    rel = st.multiselect(
        "PBL 관련성", ["high", "medium", "low", "unknown"],
        default=["high", "medium"],
    )
    st.divider()
    st.caption(f"전체 {all_count}건 · 차단 {len(BLOCKED)}건 · 표시 {len(docs)}건")
    if BLOCKED:
        with st.expander("차단된 URL 보기"):
            for u in config.BLOCKED_URLS:
                st.code(u, language=None)
    st.markdown(f"[config.py 편집 (GitHub)]({GITHUB_EDIT_URL})")

filtered = [d for d in docs if d["source"] in pick]
if query:
    q = query.lower()
    filtered = [
        d for d in filtered
        if q in (d["summary_json"] or "").lower() or q in (d["title"] or "").lower()
    ]
if rel:
    def _rel(d):
        try:
            return json.loads(d["summary_json"] or "{}").get("PBL관련성", "unknown")
        except Exception:
            return "unknown"
    filtered = [d for d in filtered if _rel(d) in rel]

st.caption(f"{len(filtered)} / {len(docs)} 건")

for d in filtered:
    try:
        s = json.loads(d["summary_json"] or "{}")
    except Exception:
        s = {}
    with st.container(border=True):
        st.markdown(f"**[{d['source']}]** {d.get('title') or '(제목 없음)'}")
        if s.get("한줄요약"):
            st.markdown(f"> {s['한줄요약']}")
        col1, col2 = st.columns([3, 1])
        with col1:
            for p in s.get("핵심포인트") or []:
                st.markdown(f"- {p}")
            if s.get("관련성근거"):
                st.caption(s["관련성근거"])
        with col2:
            st.markdown(f"**관련성**: {s.get('PBL관련성', '?')}")
            kws = s.get("주요키워드") or []
            if kws:
                st.markdown("**키워드**: " + ", ".join(kws))
        st.markdown(f"[원문]({d['url']})")
        with st.expander("이 자료 차단하기"):
            st.code(f'    "{d["url"]}",', language=None)
            st.markdown(
                f"위 줄을 복사 → [config.py 편집]({GITHUB_EDIT_URL}) → "
                f"`BLOCKED_URLS` 리스트 안에 붙여넣고 Commit. "
                f"다음 GHA 실행부터 적용되고, 화면에서는 즉시 사라집니다."
            )
