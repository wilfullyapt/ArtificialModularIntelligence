"""python -m ami.neighbors_directory --host 0.0.0.0 --port 4178"""

from __future__ import annotations

import argparse
import os
import sys

from .server import serve_directory
from .store import DirectoryStore


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ami.neighbors_directory", description="AMI neighbors directory server")
    p.add_argument("--host", default=os.environ.get("AMI_DIRECTORY_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.environ.get("AMI_DIRECTORY_PORT", "4178")))
    p.add_argument("--data", default=os.environ.get("AMI_DIRECTORY_DATA", ""), help="JSON peer store path")
    p.add_argument("--token", default=os.environ.get("AMI_NEIGHBORS_TOKEN", ""), help="Bearer token (optional)")
    p.add_argument("--ttl", type=float, default=float(os.environ.get("AMI_DIRECTORY_TTL", "3600")))
    args = p.parse_args(argv)

    store = DirectoryStore(args.data or None, ttl_seconds=args.ttl)
    httpd = serve_directory(host=args.host, port=args.port, store=store, token=args.token or None)
    print(f"ami-neighbors-directory listening on http://{args.host}:{args.port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down", flush=True)
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
