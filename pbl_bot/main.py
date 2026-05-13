import argparse
import json

from . import config
from .daily_run import run
from .storage import Storage


def cmd_run(args):
    run(args.max)


def cmd_list(args):
    store = Storage(config.DB_PATH)
    docs = store.all_summarized()[: args.limit]
    if not docs:
        print("(요약된 문서 없음)")
        return
    for doc in docs:
        s = json.loads(doc["summary_json"] or "{}")
        print(f"- [{doc['source']}] {doc.get('title') or '(제목 없음)'}")
        print(f"  {s.get('한줄요약','(요약 없음)')}")
        print(f"  관련성: {s.get('PBL관련성','?')}  |  {doc['url']}")
        print()


def cmd_stats(args):
    store = Storage(config.DB_PATH)
    for k, v in store.counts().items():
        print(f"{k}: {v}")


def main():
    p = argparse.ArgumentParser(prog="pbl-bot")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="discovery + summarize")
    pr.add_argument("--max", type=int, default=config.MAX_PER_RUN)
    pr.set_defaults(func=cmd_run)

    pl = sub.add_parser("list", help="list summarized docs")
    pl.add_argument("--limit", type=int, default=20)
    pl.set_defaults(func=cmd_list)

    ps = sub.add_parser("stats", help="show document counts by status")
    ps.set_defaults(func=cmd_stats)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
