from __future__ import annotations

import argparse
import json
import os
import sys

from app.config import settings
from app.service import AgentService


def main() -> None:
    parser = argparse.ArgumentParser(description="企业制度与报销助手")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="导入 Markdown/PDF 制度")
    ask_parser = sub.add_parser("ask", help="询问助手")
    ask_parser.add_argument("question")
    sub.add_parser("eval", help="运行离线评测")
    sub.add_parser("serve", help="启动 FastAPI")
    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn

        uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=False)
        return

    service = AgentService(settings)
    if args.command == "ingest":
        print(json.dumps({"indexed_chunks": service.ingest()}, ensure_ascii=False))
    elif args.command == "ask":
        state = service.chat(args.question, "cli-session", "E1001")
        print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "eval":
        from evals.evaluate import run_evaluation

        print(json.dumps(run_evaluation(service), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
