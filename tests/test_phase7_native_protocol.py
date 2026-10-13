"""Focused offline check of the installed Codex protocol inside existing OCI isolation."""

import json
import shutil
import subprocess
import uuid
from pathlib import Path
import pytest
from jarvis.coding_agents import oci, runs, transport

PROBE = r"""
import json, subprocess, os
binary = os.environ['ARIA_FIXTURE_CODEX']
# Supported custom-provider configuration for this offline protocol fixture only.
# Private loopback has no listener and no credentials; no external inference can run.
config=['-c','model_provider="aria_offline_fixture"',
        '-c','model_providers.aria_offline_fixture.name="Offline fixture"',
        '-c','model_providers.aria_offline_fixture.base_url="http://127.0.0.1:1/v1"',
        '-c','model_providers.aria_offline_fixture.wire_api="responses"',
        '-c','model_providers.aria_offline_fixture.requires_openai_auth=false']
thread = None
for iteration in range(2):
    proc = subprocess.Popen([binary,'app-server','--listen','stdio://','-c','memories.use_memories=false','-c','memories.generate_memories=false',*config],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    notifications=[]
    def call(identity, method, params):
        proc.stdin.write(json.dumps({'id':identity,'method':method,'params':params})+'\n');proc.stdin.flush()
        while True:
            line=proc.stdout.readline()
            if not line:raise RuntimeError('native server ended')
            row=json.loads(line)
            if row.get('method') and 'id' not in row:notifications.append(row)
            if row.get('id')==identity:
                if 'error' in row:raise RuntimeError(str(row['error']))
                return row['result']
    call(1,'initialize',{'clientInfo':{'name':'aria-phase7-fixture','version':'1'},'capabilities':{'experimentalApi':True}})
    proc.stdin.write('{"method":"initialized"}\n');proc.stdin.flush()
    params={'cwd':os.getcwd(),'approvalPolicy':'never','sandbox':'read-only'}
    if thread:params['threadId']=thread
    else:params['ephemeral']=False
    result=call(2,'thread/resume' if thread else 'thread/start',params)
    assert not result['thread'].get('ephemeral')
    if thread:assert result['thread']['id']==thread
    thread=result['thread']['id']
    if iteration==0:
        turn=call(3,'turn/start',{'threadId':thread,'input':[{'type':'text','text':'Offline interruption fixture','text_elements':[]}],
            'sandboxPolicy':{'type':'externalSandbox','networkAccess':'enabled'},'approvalPolicy':'never'})['turn']['id']
        try:call(4,'turn/interrupt',{'threadId':thread,'turnId':turn})
        except RuntimeError as exc:
            # A denied offline transport can finish before the interrupt arrives.
            if 'no active turn to interrupt' not in str(exc):raise
        while not any(x.get('method')=='turn/completed' for x in notifications):
            line=proc.stdout.readline()
            if not line:raise RuntimeError('native interrupt did not finish')
            event=json.loads(line)
            if event.get('method')=='turn/completed':break
    proc.stdin.close();proc.wait(timeout=5)
print(json.dumps({'native_thread_resume':True,'process_restarts':1,'external_inference_requests':0}))
"""


def test_installed_codex_durable_resume_after_offline_turn(tmp_path):
    binary = Path("/home/jeff/.nvm/versions/node/v24.15.0/bin/codex")
    if not binary.is_file() or not shutil.which("docker"):
        pytest.skip("native Codex/OCI not installed")
    image = oci.image_id("ollama/ollama:latest")
    ws = tmp_path / "workspace"
    out = tmp_path / "out"
    state = tmp_path / "private-codex"
    for p in [ws, out, state]:
        p.mkdir(mode=0o700)
    run_id = "phase7-protocol-" + uuid.uuid4().hex[:12]
    broker = transport.Broker("codex", tmp_path / "network.jsonl")
    broker.allowed = frozenset()  # This offline check may not reach any external host.
    cid = ""
    # command/exec runs an offline protocol harness; no auth is mounted.
    script = 'import os; os.environ["ARIA_FIXTURE_CODEX"]=' + repr(str(binary)) + ";" + PROBE
    try:
        cid = oci.create(
            run_id=run_id,
            image=image,
            ws=str(ws),
            out_dir=str(out),
            request={
                "agent": "codex",
                "binary": str(binary),
                "cwd": str(ws),
                "out_dir": str(out),
                "timeout_s": 30,
                "command": ["/usr/bin/python3", "-c", script],
            },
            installations=runs._install_dirs(str(binary)),
            bindings=[(str(state), str(Path.home() / ".codex"))],
            socket_path=broker.path,
            read_only=True,
        )
        result = subprocess.run([*oci.DOCKER, "start", "--attach", cid], capture_output=True, text=True, timeout=35)
        assert result.returncode == 0, (result.stdout, result.stderr)
        records = [json.loads(x) for x in result.stdout.splitlines() if x.startswith("{")]
        command = next(x["result"] for x in records if x.get("type") == "certification.command")
        assert command["exitCode"] == 0, command
        assert '"native_thread_resume": true' in command["stdout"]
        if broker.log.exists():
            assert not [json.loads(x) for x in broker.log.read_text().splitlines() if json.loads(x).get("decision") == "allow"]
    finally:
        if cid:
            oci.remove(cid, run_id)
        broker.close()
