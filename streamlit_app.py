import json
import sqlite3
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "pbl.db"

st.set_page_config(page_title="PBL Watch", layout="wide")
st.title("PBL Watch — Performance Based Logistics 자료 모음")

if not DB_PATH.exists():
    st.info("아직 데이터가 없습니다. 먼저 `python -m pbl_bot.main run` 을 실행하세요.")
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

if not docs:
    st.info("수집된 문서는 있지만 아직 요약된 게 없습니다.")
    st.stop()

sources = sorted({d["source"] for d in docs})
pick = st.sidebar.multiselect("소스", sources, default=sources)
query = st.sidebar.text_input("키워드 필터")
rel = st.sidebar.multiselect(
    "PBL 관련성", ["high", "medium", "low", "unknown"],
    default=["high", "medium"],
)

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
        st.markdown(f"[원문 PDF]({d['url']})")
