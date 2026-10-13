#!/usr/bin/env python3
"""Rotate ARIA's LAN API key, Home Assistant token and automation webhook secret.

Run it yourself in a terminal (not through an AI assistant's shell, whose output
is recorded):

    venv/bin/python scripts/rotate-credentials.py --all

* Nothing secret is printed. The new LAN API key is written to a 0600 file for you
  to copy into LAN clients; the HA token and master password are read with hidden
  input.
* data/jarvis.env is backed up (0600) before any change; the Owner Vault copies of
  ``lan.api_key`` and ``ha.token`` are updated when the vault is unlocked with your
  master password, so the env and vault never disagree.
* A new HA token is tested against Home Assistant before anything is saved.

Afterwards: revoke the OLD token in Home Assistant, update webhook callers with the
new automation secret, then restart:  systemctl --user restart jarvis.service aria-tray.service
"""
from __future__ import annotations

import argparse
import getpass
import os
import shutil
import stat
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _private_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    os.chmod(dst, stat.S_IRUSR | stat.S_IWUSR)


def _write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(text)


def _unlock_vault():
    """The unlocked Owner Security service, or None when no vault entry needs it."""
    from jarvis.security.owner.provider_credentials import bound_owner_service

    svc = bound_owner_service()
    if not svc.vault.exists():
        return None
    for attempt in range(3):
        result = svc.unlock(getpass.getpass("Owner Vault master password: "))
        if svc.vault.is_unlocked():
            return svc
        print(f"  Not unlocked ({(result or {}).get('message', 'wrong password')}).")
    raise SystemExit("Vault stayed locked; nothing was changed.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lan-api-key", action="store_true", help="new random JARVIS_API_KEY")
    ap.add_argument("--automation-secret", action="store_true", help="new random JARVIS_AUTOMATION_SECRET")
    ap.add_argument("--ha-token", action="store_true", help="new Home Assistant long-lived token (you paste it)")
    ap.add_argument("--all", action="store_true", help="all three")
    ap.add_argument("--env-file", default="", help="env file to rotate (default: ARIA's data/jarvis.env)")
    args = ap.parse_args()
    if args.all:
        args.lan_api_key = args.automation_secret = args.ha_token = True
    if not (args.lan_api_key or args.automation_secret or args.ha_token):
        ap.error("choose --lan-api-key, --automation-secret, --ha-token or --all")

    from jarvis import env_loader
    from jarvis.lan import generate_api_key

    if args.env_file:
        env_loader.ENV_FILE = Path(args.env_file).resolve()  # upsert_env_vars writes this file
    else:
        env_loader.load_jarvis_env()
    env_file = Path(env_loader.ENV_FILE)
    data_dir = env_file.parent
    if not env_file.is_file():
        raise SystemExit(f"{env_file} not found; nothing to rotate.")

    updates: dict[str, str] = {}
    vault_fields: dict[str, str] = {}

    if args.ha_token:
        from jarvis.home_assistant import ha_url, normalize_ha_token, test_connection

        print("Create a new long-lived token in Home Assistant: Profile → Security → Long-lived access tokens.")
        token = normalize_ha_token(getpass.getpass("New Home Assistant token (hidden): "))
        if not token:
            raise SystemExit("No token entered; nothing was changed.")
        probe = test_connection(ha_url(), token)
        if not probe.get("ok"):
            raise SystemExit(f"Home Assistant rejected the new token ({probe.get('message', 'failed')}); "
                             "nothing was changed.")
        updates["JARVIS_HA_TOKEN"] = token
        vault_fields["ha_token"] = token
        print("  New HA token works.")
    if args.lan_api_key:
        key = generate_api_key()
        updates["JARVIS_API_KEY"] = key
        vault_fields["lan_api_key"] = key
    if args.automation_secret:
        updates["JARVIS_AUTOMATION_SECRET"] = generate_api_key()

    from jarvis.security.owner.provider_credentials import bound_owner_service, vault_has_entry

    vault_ids = {"lan_api_key": "lan.api_key", "ha_token": "ha.token"}
    owner = bound_owner_service()
    needs_vault = any(vault_has_entry(owner, vault_ids[field]) for field in vault_fields)
    svc = _unlock_vault() if needs_vault else None

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = data_dir / "backups" / f"jarvis.env.before-rotation-{stamp}"
    _private_copy(env_file, backup)
    print(f"Backed up {env_file.name} → {backup} (0600)")

    if svc is not None:
        from jarvis.security.owner.provider_credentials import sync_vault_secret_if_migrated

        for field, value in vault_fields.items():
            result = sync_vault_secret_if_migrated(field, value)
            if not result.get("ok"):
                raise SystemExit(f"Vault update for {field} failed ({result.get('reason')}); "
                                 f"jarvis.env unchanged, backup at {backup}.")
            print(f"  Owner Vault: {field} {'updated' if result.get('synced') else 'not migrated (env only)'}")
    env_loader.upsert_env_vars(updates)
    os.chmod(env_file, stat.S_IRUSR | stat.S_IWUSR)
    for name in updates:
        print(f"  jarvis.env: {name} replaced")

    try:
        from jarvis.integrations_product.secrets_bus import mark_rotated

        for name in updates:
            mark_rotated(name.lower())
    except Exception:  # noqa: BLE001 - bookkeeping only
        pass

    if "JARVIS_API_KEY" in updates:
        out = data_dir / "security" / f"new-lan-api-key-{stamp}.txt"
        _write_private(out, updates["JARVIS_API_KEY"] + "\n")
        print(f"\nNew LAN API key saved to {out} (0600). Copy it into LAN clients, then delete the file.")
    if "JARVIS_AUTOMATION_SECRET" in updates:
        print("Update Home Assistant / n8n webhook callers: header X-Jarvis-Automation-Secret "
              "(value is in data/jarvis.env).")
    if "JARVIS_HA_TOKEN" in updates:
        print("Now revoke the OLD token in Home Assistant (Profile → Security).")
    print("\nRestart to apply:  systemctl --user restart jarvis.service aria-tray.service")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
