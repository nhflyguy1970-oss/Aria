"""Subscription CONNECT broker. The sandbox has no routable network or host DNS.

Only exact first-party TLS authorities are accepted; resolved private/local
addresses are rejected. Neither TLS payloads nor authentication headers are
inspected or logged. A private Unix socket is the only host communication path.
"""

from __future__ import annotations

import ipaddress
import json
import select
import socket
import socketserver
import tempfile
import threading
from pathlib import Path

HOSTS = {
    "codex": frozenset({"chatgpt.com", "auth.openai.com"}),
    "claude_code": frozenset({"api.anthropic.com", "claude.ai"}),
    "antigravity": frozenset({"cloudcode-pa.googleapis.com", "oauth2.googleapis.com"}),
}


def authority(request: bytes, allowed: frozenset[str]) -> str:
    line = request.split(b"\r\n", 1)[0].decode("ascii")
    parts = line.split(" ")
    if len(parts) != 3 or parts[0] != "CONNECT" or parts[2] not in ("HTTP/1.0", "HTTP/1.1"):
        raise ValueError("only CONNECT is permitted")
    host, separator, port = parts[1].rpartition(":")
    if separator != ":" or port != "443" or host not in allowed:
        raise ValueError("TLS authority is not allowlisted")
    return host


def public_addresses(host: str) -> list[tuple]:
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("DNS returned a non-public address")
    return addresses


def client_hello(client: socket.socket, expected_host: str) -> bytes:
    """Bind the CONNECT authority to plaintext TLS SNI before forwarding bytes.

    A CDN address is shared infrastructure: CONNECT alone cannot prevent
    domain fronting. Reject non-TLS, missing/mismatched SNI and encrypted SNI.
    Retain no handshake or application payload in audit records.
    """

    def receive(n):
        data = b""
        while len(data) < n:
            part = client.recv(n - len(data))
            if not part:
                raise ValueError("incomplete TLS ClientHello")
            data += part
        return data

    wire = b""
    handshake = b""
    for _ in range(8):
        header = receive(5)
        size = int.from_bytes(header[3:5], "big")
        if (
            header[0] != 22
            or header[1:3] not in (b"\x03\x01", b"\x03\x02", b"\x03\x03")
            or not 0 < size <= 18432
        ):
            raise ValueError("only a bounded TLS handshake is permitted")
        body = receive(size)
        wire += header + body
        handshake += body
        if len(handshake) >= 4:
            wanted = 4 + int.from_bytes(handshake[1:4], "big")
            if handshake[0] != 1 or wanted > 65536:
                raise ValueError("invalid TLS ClientHello")
            if len(handshake) >= wanted:
                break
    else:
        raise ValueError("TLS ClientHello record limit")
    data = handshake[4:wanted]
    try:
        i = 34
        i += 1 + data[i]  # legacy session ID
        size = int.from_bytes(data[i : i + 2], "big")
        i += 2 + size  # cipher suites
        i += 1 + data[i]  # compression methods
        end = i + 2 + int.from_bytes(data[i : i + 2], "big")
        i += 2
        if end != len(data):
            raise ValueError("invalid TLS extensions")
        names = []
        while i < end:
            kind = int.from_bytes(data[i : i + 2], "big")
            length = int.from_bytes(data[i + 2 : i + 4], "big")
            extension = data[i + 4 : i + 4 + length]
            if len(extension) != length:
                raise ValueError("truncated TLS extension")
            if kind == 0xFE0D:
                raise ValueError("encrypted SNI is not permitted")
            if kind == 0:
                if int.from_bytes(extension[:2], "big") != len(extension) - 2:
                    raise ValueError("invalid SNI list")
                j = 2
                while j < len(extension):
                    name_length = int.from_bytes(extension[j + 1 : j + 3], "big")
                    if extension[j] != 0 or j + 3 + name_length > len(extension):
                        raise ValueError("invalid SNI name")
                    names.append(extension[j + 3 : j + 3 + name_length].decode("ascii"))
                    j += 3 + name_length
            i += 4 + length
        if names != [expected_host]:
            raise ValueError("TLS SNI does not match the approved authority")
    except (IndexError, UnicodeError) as exc:
        raise ValueError("invalid TLS ClientHello") from exc
    return wire


def relay(left: socket.socket, right: socket.socket, timeout: int = 300) -> None:
    while True:
        ready, _, _ = select.select([left, right], [], [], timeout)
        if not ready:
            return
        for source in ready:
            chunk = source.recv(65536)
            if not chunk:
                return
            (right if source is left else left).sendall(chunk)


class Broker:
    def __init__(self, agent: str, log: Path):
        self.allowed = HOSTS[agent]
        self.log = log
        self.temp = tempfile.TemporaryDirectory(prefix="aria-agent-net-")
        self.path = str(Path(self.temp.name) / "proxy.sock")
        self.lock = threading.Lock()
        self.slots = threading.BoundedSemaphore(8)
        self.connections = set()
        self.closing = False
        broker = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                if not broker.slots.acquire(blocking=False):
                    broker.record("deny", "", "connection limit")
                    return
                try:
                    with broker.lock:
                        if broker.closing:
                            return
                        broker.connections.add(self.request)
                    self.request.settimeout(15)
                    request = b""
                    while b"\r\n\r\n" not in request and len(request) <= 8192:
                        data = self.request.recv(1024)
                        if not data:
                            return
                        request += data
                    if len(request) > 8192 or not request.endswith(b"\r\n\r\n"):
                        raise ValueError("invalid CONNECT framing")
                    host = authority(request, broker.allowed)
                    addresses = public_addresses(host)
                    target = None
                    for family, kind, protocol, _, address in addresses:
                        candidate = socket.socket(family, kind, protocol)
                        candidate.settimeout(15)
                        try:
                            candidate.connect(address)
                            target = candidate
                            break
                        except OSError:
                            candidate.close()
                    if target is None:
                        raise OSError("provider connection failed")
                    with target:
                        with broker.lock:
                            broker.connections.add(target)
                        self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                        hello = client_hello(self.request, host)
                        target.sendall(hello)
                        broker.record("allow", host, "public TLS destination; SNI verified")
                        relay(self.request, target)
                except (ValueError, UnicodeError, OSError) as exc:
                    broker.record("deny", "", str(exc))
                    try:
                        self.request.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                    except OSError:
                        pass
                finally:
                    with broker.lock:
                        broker.connections.discard(self.request)
                        if "target" in locals() and target is not None:
                            broker.connections.discard(target)
                    broker.slots.release()

        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads = True

        self.server = Server(self.path, Handler)
        Path(self.path).chmod(0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def record(self, decision: str, host: str, reason: str) -> None:
        with self.lock:
            self.log.parent.mkdir(parents=True, exist_ok=True)
            with self.log.open("a") as file:
                file.write(
                    json.dumps({"decision": decision, "host": host, "reason": reason}) + "\n"
                )
            self.log.chmod(0o600)

    def close(self) -> None:
        with self.lock:
            self.closing = True
            for connection in self.connections:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()


def bridge(path: str) -> tuple[socketserver.TCPServer, str]:
    """Inside the private network namespace: loopback proxy -> Unix broker."""

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as target:
                    target.connect(path)
                    relay(self.request, target)
            except OSError:
                pass  # peer disconnects are ordinary transport closure

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True

    server = Server(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"
