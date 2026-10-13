"""ARIA-specific, opt-in public-client Sign in with ChatGPT.

No Codex credentials are read. Login performs authentication only, never inference.
Tokens use protected local runtime storage; inference additionally requires the
unlocked Owner Vault and the existing cloud disclosure/authorization boundary.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import stat
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser

from jarvis.config import DATA_DIR
from jarvis.inference.providers.base import ProviderAuthError

ISSUER = "https://auth.openai.com"
RESOURCE = "https://api.openai.com/v1"
AUTHORIZE = ISSUER + "/api/accounts/authorize"
TOKEN = ISSUER + "/api/accounts/oauth/token"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
STORE = DATA_DIR / "chatgpt_oauth"
_MUTEX = threading.RLock()


def enabled() -> bool:
    mode = os.environ.get("JARVIS_OPENAI_AUTH_MODE", "api").strip().lower()
    if mode not in ("api", "chatgpt_plan"):
        raise ProviderAuthError("OpenAI: invalid authentication mode")
    return mode == "chatgpt_plan"


def _private(path: Path, *, directory=False):
    info = path.lstat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077 or (not directory and info.st_nlink != 1):
        raise ProviderAuthError("ChatGPT: insecure credential storage permissions")
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise ProviderAuthError("ChatGPT: invalid credential storage")


def _read(name: str) -> dict:
    path = STORE / name
    _private(STORE, directory=True)
    _private(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        return json.load(stream)


def _write(name: str, value: dict):
    _private(STORE, directory=True)
    fd, tmp = tempfile.mkstemp(prefix=".pending-", dir=STORE)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, STORE / name)
        dfd = os.open(STORE, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextmanager
def _locked():
    with _MUTEX:
        STORE.mkdir(mode=0o700, parents=True, exist_ok=True)
        _private(STORE, directory=True)
        fd = os.open(STORE / ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            _private(STORE / ".lock")
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _json_request(url: str, fields: dict | None = None) -> dict:
    if urllib.parse.urlsplit(url).scheme != "https" or urllib.parse.urlsplit(url).netloc != "auth.openai.com":
        raise ProviderAuthError("ChatGPT: refusing an untrusted authentication endpoint")
    body = urllib.parse.urlencode(fields).encode() if fields is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"} if body else {})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=20) as response:
            return json.load(response)
    except Exception:
        # Token responses/errors and URLs must never appear in diagnostics.
        raise ProviderAuthError("ChatGPT: authentication request failed; sign in again if the session expired") from None


def _validate_id(token: str, client_id: str, nonce: str | None) -> dict:
    import jwt
    try:
        discovery = _json_request(ISSUER + "/.well-known/openid-configuration")
        if discovery.get("issuer") != ISSUER:
            raise ValueError("issuer")
        jwks = _json_request(discovery["jwks_uri"])
        header = jwt.get_unverified_header(token)
        if header.get("alg") != "RS256":
            raise ValueError("algorithm")
        key = next(k for k in jwks["keys"] if k.get("kid") == header.get("kid") and k.get("kty") == "RSA")
        claims = jwt.decode(token, jwt.PyJWK.from_dict(key).key, algorithms=["RS256"], audience=client_id, issuer=ISSUER,
                            options={"require": ["iss", "aud", "exp", "sub"]})
        if not claims.get("sub") or nonce is not None and not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
            raise ValueError("identity")
        return claims
    except Exception:
        raise ProviderAuthError("ChatGPT: ID token validation failed") from None


def _session(tokens: dict, *, client_id: str, host_id: str, nonce: str | None, previous: dict | None = None) -> dict:
    if not client_id or client_id == "dynamic_agent_client":
        raise ProviderAuthError("ChatGPT: registration did not issue a client ID")
    claims = _validate_id(tokens.get("id_token", ""), client_id, nonce)
    if previous and (claims["sub"] != previous["subject"] or client_id != previous["client_id"]):
        raise ProviderAuthError("ChatGPT: account mismatch; existing connection preserved")
    scopes = str(tokens.get("scope", "")).split()
    if not {"resource.invoke", "chatgpt.tokens.use.direct", "offline_access"}.issubset(scopes):
        raise ProviderAuthError("ChatGPT: plan usage permission was not granted")
    if tokens.get("token_type", "").lower() != "bearer" or not all(tokens.get(k) for k in ("access_token", "refresh_token")):
        raise ProviderAuthError("ChatGPT: incomplete renewable session")
    try:
        lifetime = float(tokens["expires_in"])
        if not 0 < lifetime <= 86400:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise ProviderAuthError("ChatGPT: invalid token expiry") from None
    return {"issuer": ISSUER, "subject": claims["sub"], "client_id": client_id, "ext_agent_host_id": host_id,
            "id_token": tokens["id_token"], "access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer", "scopes": scopes, "expires_at": time.time() + lifetime,
            "earliest_refresh_at": tokens.get("earliest_refresh_at"),
            "plan_only_confirmed": bool(previous and nonce is None and previous.get("plan_only_confirmed"))}


def _owner_check():
    from jarvis.security.owner import get_owner_security
    if not get_owner_security().authorize("vault.secret.use", room="integrations").get("ok"):
        raise ProviderAuthError("ChatGPT: Owner Vault is locked or permission was denied")


def sensitive_values() -> list[str]:
    """Local disclosure guard only; never refresh, log, or expose tokens in HTTP."""
    try:
        _owner_check()
        s = _read("session.json")
        return [s[k] for k in ("access_token", "refresh_token", "id_token") if isinstance(s.get(k), str) and len(s[k]) >= 8]
    except Exception:
        return []


def status() -> dict:
    try:
        _owner_check()
        if not (STORE / "session.json").exists():
            return {"state": "unconfigured", "source": "aria_oauth"}
        s = _read("session.json")
        if not {"resource.invoke", "chatgpt.tokens.use.direct"}.issubset(s.get("scopes", [])) or not s.get("refresh_token") or not s.get("plan_only_confirmed"):
            return {"state": "unconfigured", "source": "aria_oauth"}
        return {"state": "credentials_present", "source": "aria_oauth", "expires_at": s["expires_at"]}
    except Exception:
        return {"state": "locked_or_invalid", "source": "aria_oauth"}


def access_token() -> str:
    _owner_check()
    try:
        with _locked():
            s = _read("session.json")
            if not s.get("plan_only_confirmed"):
                raise ProviderAuthError("ChatGPT: disable ARIA credits in ChatGPT Settings > Usage, then confirm-plan-only")
            if not {"resource.invoke", "chatgpt.tokens.use.direct"}.issubset(s.get("scopes", [])):
                raise ProviderAuthError("ChatGPT: plan usage is not authorized")
            if float(s["expires_at"]) <= time.time() + 60:
                earliest = s.get("earliest_refresh_at")
                if earliest is not None and float(earliest) > time.time():
                    raise ProviderAuthError("ChatGPT: token refresh is not permitted yet")
                tokens = _json_request(TOKEN, {"grant_type": "refresh_token", "client_id": s["client_id"],
                                              "refresh_token": s["refresh_token"], "resource": RESOURCE})
                s = _session(tokens, client_id=s["client_id"], host_id=s["ext_agent_host_id"], nonce=None, previous=s)
                _write("session.json", s)
            _owner_check()
            return s["access_token"]
    except ProviderAuthError:
        raise
    except Exception:
        raise ProviderAuthError("ChatGPT: connection unavailable; authorize ARIA with login") from None


def begin(redirect_uri: str) -> dict:
    parsed = urllib.parse.urlsplit(redirect_uri)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path != "/auth/callback" or not parsed.port or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ProviderAuthError("ChatGPT: invalid loopback callback")
    with _locked():
        try:
            host = _read("host.json")
        except FileNotFoundError:
            host = {"ext_agent_host_id": "urn:uuid:" + str(uuid.uuid4())}
            _write("host.json", host)
        try:
            old = _read("session.json")
        except FileNotFoundError:
            old = None
    verifier = secrets.token_urlsafe(48)
    pending = {"state": secrets.token_urlsafe(32), "nonce": secrets.token_urlsafe(32), "verifier": verifier,
               "redirect_uri": redirect_uri, "host_id": host["ext_agent_host_id"], "previous": old,
               "client_id": old["client_id"] if old else "dynamic_agent_client", "deadline": time.monotonic() + 600}
    params = {"client_id": pending["client_id"], "ext_agent_host_id": pending["host_id"], "response_type": "code",
              "redirect_uri": redirect_uri, "scope": SCOPES, "resource": RESOURCE, "state": pending["state"],
              "nonce": pending["nonce"], "code_challenge_method": "S256",
              "code_challenge": base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")}
    if not old:
        params["agent_name_hint"] = "ARIA"
    # No ID-token hint in printed browser URLs; returning owners choose their account.
    pending["url"] = AUTHORIZE + "?" + urllib.parse.urlencode(params)
    return pending


def finish(pending: dict, query: dict):
    if pending.get("consumed") or time.monotonic() > pending["deadline"]:
        raise ProviderAuthError("ChatGPT: authorization attempt expired or was already used")
    state = query.get("state", "")
    if not isinstance(state, str) or not secrets.compare_digest(state, pending["state"]):
        raise ProviderAuthError("ChatGPT: invalid authorization state")
    pending["consumed"] = True
    if query.get("error"):
        raise ProviderAuthError("ChatGPT: owner consent was not granted")
    client_id = query.get("client_id") or pending["client_id"]
    if client_id == "dynamic_agent_client" or pending["previous"] and client_id != pending["client_id"]:
        raise ProviderAuthError("ChatGPT: callback registration mismatch")
    if not query.get("code"):
        raise ProviderAuthError("ChatGPT: authorization code missing")
    tokens = _json_request(TOKEN, {"grant_type": "authorization_code", "client_id": client_id, "code": query["code"],
                                 "code_verifier": pending["verifier"], "redirect_uri": pending["redirect_uri"], "resource": RESOURCE})
    s = _session(tokens, client_id=client_id, host_id=pending["host_id"], nonce=pending["nonce"], previous=pending["previous"])
    with _locked():
        try:
            current = _read("session.json")
        except FileNotFoundError:
            current = None
        if current and (current["subject"] != s["subject"] or current["client_id"] != s["client_id"]):
            raise ProviderAuthError("ChatGPT: another account is active; existing connection preserved")
        _write("session.json", s)


def login():
    result = {}
    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Callback URLs contain authorization codes.
        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != "/auth/callback":
                self.send_error(404)
                return
            try:
                raw = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
                if any(len(v) != 1 for v in raw.values()):
                    raise ValueError()
                finish(pending, {k: v[0] for k, v in raw.items()})
                message = "ARIA ChatGPT authorization saved. You may close this tab. Inference remains disabled."
                result["ok"] = True
            except Exception:
                message = "ARIA authorization failed or was declined. No connection was replaced."
                result["failed"] = True
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(message.encode())
    with HTTPServer(("127.0.0.1", 0), Callback) as server:
        pending = begin(f"http://127.0.0.1:{server.server_port}/auth/callback")
        print("Continue with ChatGPT: approve ARIA and ChatGPT plan use in your browser.\n"
              "Use your Plus account. Allow included plan usage only; disable credits for ARIA in ChatGPT Settings > Usage.\n"
              "No inference request will be sent by this command.\n" + pending["url"])
        webbrowser.open(pending["url"])
        server.timeout = 1
        while time.monotonic() <= pending["deadline"] and not result:
            server.handle_request()
    if not result.get("ok"):
        raise ProviderAuthError("ChatGPT: authorization was not completed; existing connection preserved")
    print("ARIA-specific authorization saved securely. API credentials and inference settings are unchanged.")


def main():
    parser = argparse.ArgumentParser(description="ARIA-specific Sign in with ChatGPT; authentication only")
    parser.add_argument("command", choices=["login", "status", "confirm-plan-only"])
    args = parser.parse_args()
    try:
        if args.command == "login":
            login()
        elif args.command == "confirm-plan-only":
            print("In ChatGPT Settings > Usage, disable ARIA credit usage and permit included plan usage only.")
            if input("After checking those provider-side limits, type ARIA credits are disabled: ") != "ARIA credits are disabled":
                raise ProviderAuthError("ChatGPT: plan-only confirmation was not completed")
            with _locked():
                s = _read("session.json")
                s["plan_only_confirmed"] = True
                _write("session.json", s)
            print("Plan-only setting acknowledged; inference remains subject to ARIA owner/cloud protections.")
        else:
            print(json.dumps(status()))
    except ProviderAuthError as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
