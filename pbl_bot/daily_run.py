import logging
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from . import config
from .annotator_ollama import summarize
from .processor import fetch_text
from .relevance import classify
from .scrapers import all_sources
from .storage import Storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("daily_run")


def run(max_docs: int = config.MAX_PER_RUN):
    store = Storage(config.DB_PATH)

    log.info("=== 1) Discovery ===")
    discoveries = all_sources()
    new = 0
    for d in discoveries:
        if store.upsert_discovery(d["source"], d["url"], d.get("title"), d.get("published")):
            new += 1
    log.info("found %d items, %d new", len(discoveries), new)

    log.info("=== 2) Process up to %d ===", max_docs)
    pending = store.pending(max_docs)
    if not pending:
        log.info("nothing to process")
        return

    for doc in pending:
        log.info("→ [%s] %s", doc["source"], doc["url"])
        try:
            text = fetch_text(doc["url"])
            body = text.strip()
            if not body:
                store.mark_failed(doc["id"], "empty text")
                continue

            if len(body) < config.MIN_BODY_CHARS:
                log.info("  short body (%d chars) → relevance=low", len(body))
                summary = summarize(text)
                summary["PBL관련성"] = "low"
                summary["_short_body"] = True
            else:
                summary = summarize(text)
                summary["PBL관련성"] = classify(text, doc.get("title") or "")

            store.save_summary(doc["id"], summary, text[:2000])
            log.info("  ok [%s]: %s", summary["PBL관련성"], str(summary.get("한줄요약", ""))[:80])
        except Exception as e:
            log.exception("  failed")
            store.mark_failed(doc["id"], str(e))

    log.info("=== counts: %s ===", store.counts())


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else config.MAX_PER_RUN
    run(n)
