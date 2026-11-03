from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve an Agent Assurance report locally.")
    parser.add_argument("--report", type=Path, default=Path("report.html"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    report = args.report.resolve()
    if not report.is_file():
        parser.error(f"Report does not exist: {report}")

    class ReportHandler(SimpleHTTPRequestHandler):
        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(report.parent), **handler_kwargs)

        def do_GET(self):
            if self.path in {"/", "/index.html"}:
                self.path = "/" + report.name
            return super().do_GET()

    server = ThreadingHTTPServer((args.host, args.port), ReportHandler)
    print(f"Serving {report} at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
