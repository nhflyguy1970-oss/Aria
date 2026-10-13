"""Codex app-server protocol, using a deterministic local server; no model requests."""

import importlib.util
import json
import sys
from pathlib import Path
import pytest
from jarvis.coding_agents import transport


@pytest.mark.parametrize("resume", [False, True])
@pytest.mark.parametrize("early_notifications", [False, True])
def test_worker_persists_or_resumes_private_thread_and_denies_extra_authority(tmp_path, monkeypatch, capsys, resume, early_notifications):
    monkeypatch.setitem(sys.modules, "transport", transport)
    code = Path(__file__).resolve().parents[1] / "jarvis/coding_agents/rpc_worker.py"
    spec = importlib.util.spec_from_file_location("phase7_rpc_worker", code)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)

    class Server:
        def shutdown(self):
            pass

    monkeypatch.setattr(worker, "bridge", lambda path: (Server(), "http://127.0.0.1:1"))
    sent = []
    requests = []

    class Output:
        def readline(self):
            return json.dumps(requests.pop(0)) + "\n" if requests else ""

    class Input:
        def write(self, raw):
            msg = json.loads(raw)
            sent.append(msg)
            if "method" not in msg:
                return
            method = msg["method"]
            result = {}
            if method == "account/read":
                result = {"account": {"type": "chatgpt"}}
            if method in ("thread/start", "thread/resume"):
                result = {"thread": {"id": "private-thread"}}
            if method == "turn/start":
                # A server request can reuse our numeric ID; it is a different RPC direction.
                requests.append({"id": msg["id"], "method": "item/commandExecution/requestApproval", "params": {}})
            response = {"id": msg.get("id"), "result": result}
            if "id" in msg and not (method == "turn/start" and early_notifications):
                requests.append(response)
            if method == "turn/start":
                requests.extend(
                    [
                        {"id": 999, "method": "item/tool/requestUserInput", "params": {}},
                        {"method": "item/completed", "params": {"item": {"type": "agentMessage", "text": "A bounded report."}}},
                        {"method": "turn/completed", "params": {"turn": {"status": "completed"}}},
                    ]
                )
                if early_notifications:
                    requests.append(response)

        def close(self):
            sent.append({"fixture_closed": True})

        def flush(self):
            pass

    class Process:
        stdin = Input()
        stdout = Output()

        def kill(self):
            pytest.fail("completed native server should close gracefully")

        def wait(self, **kwargs):
            return 0

    monkeypatch.setattr(worker.subprocess, "Popen", lambda *a, **kw: Process())
    request = {
        "agent": "codex",
        "binary": "/fixture/codex",
        "cwd": "/fixture/workspace",
        "out_dir": str(tmp_path),
        "prompt": "inspect",
        "timeout_s": 120,
    }
    if resume:
        request["resume_thread_id"] = "private-thread"
    file = tmp_path / "request.json"
    file.write_text(json.dumps(request))
    monkeypatch.setattr(sys, "argv", ["rpc_worker.py", str(file)])
    assert worker.main() == 0
    assert {"fixture_closed": True} in sent
    calls = {x["method"]: x.get("params") for x in sent if x.get("method")}
    method = "thread/resume" if resume else "thread/start"
    assert calls[method]["approvalPolicy"] == "never"
    if resume:
        assert calls[method]["threadId"] == "private-thread" and "ephemeral" not in calls[method]
    else:
        assert calls[method]["ephemeral"] is False
    assert calls["turn/start"]["sandboxPolicy"] == {"type": "externalSandbox", "networkAccess": "enabled"}
    assert any(x.get("result", {}).get("decision") == "decline" for x in sent)
    assert any(x.get("error", {}).get("code") == -32601 for x in sent)
    events = [json.loads(x) for x in capsys.readouterr().out.splitlines()]
    assert sum(x["type"] == "approval.denied" for x in events) == 2
    assert events[-1]["type"] == "turn.completed"
    assert (tmp_path / "last_message.txt").read_text() == "A bounded report."


def test_rpc_methods_match_the_installed_protocol_schema():
    # Generated locally without account authentication or a model request.
    schema = json.loads((Path(__file__).parent / "fixtures/codex_app_server_fields.json").read_text())["schemas"]
    for name, fields in [
        ("ThreadStartParams", {"cwd", "ephemeral", "approvalPolicy", "sandbox"}),
        ("ThreadResumeParams", {"cwd", "threadId", "approvalPolicy", "sandbox"}),
        ("TurnStartParams", {"threadId", "cwd", "input", "sandboxPolicy", "approvalPolicy"}),
    ]:
        assert fields <= set(schema[name]["properties"])
