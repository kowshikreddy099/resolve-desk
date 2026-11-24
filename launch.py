import json
import os
import webbrowser
from pathlib import Path
from urllib.request import ProxyHandler, build_opener
from server import Handler, ThreadingHTTPServer, initialize

if __name__ == "__main__":
    initialize()
    port = int(os.environ.get("RESOLVE_PORT", "18451"))
    url = f"http://127.0.0.1:{port}/"
    try:
        http = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as error:
        try:
            with build_opener(ProxyHandler({})).open(url+"api/health", timeout=2) as response:
                existing = json.load(response) == {"service": "resolve-desk", "api": 2}
        except (ValueError, OSError):
            existing = False
        if not existing:
            raise SystemExit(f"Cannot start Resolve Desk at {url}: {error}") from error
        webbrowser.open(url)
        print(f"Opened the running Resolve Desk at {url}")
    else:
        with http:
            print(f"Resolve Desk is running at {url}. Keep this terminal open.", flush=True)
            import threading
            threading.Timer(0.4, webbrowser.open, args=(url,)).start()
            http.serve_forever()
