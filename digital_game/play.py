from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 8765


def available_port(preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("could not find an available local port")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run The Book of Loops digital player locally.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    port = available_port(args.port)
    handler = lambda *handler_args, **handler_kwargs: SimpleHTTPRequestHandler(
        *handler_args,
        directory=str(ROOT),
        **handler_kwargs,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/digital_game/"

    print(f"The Book of Loops digital player: {url}")
    print("Press Ctrl+C to stop the local server.")
    if not args.no_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
