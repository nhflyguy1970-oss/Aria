"""Focused OAuth security and subscription Responses compatibility; no live calls."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import time
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from jarvis.inference import chatgpt_oauth as auth, providers, gateway
from jarvis.inference.providers.base import ProviderAuthError, Request
from jarvis.inference.providers.openai_responses import OpenAIResponses
from test_phase4_providers import fake, allow, FakeResponse, sse, openai_completed, GPT, MSG, local_answer, KEYS


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "STORE", tmp_path / "oauth")
    monkeypatch.setattr(auth, "_owner_check", lambda: None)
    return auth.STORE


def tokens(**changes):
    result = dict(access_token="ARIA-access", refresh_token="ARIA-refresh", id_token="id", token_type="Bearer", expires_in=3600, scope=auth.SCOPES)
    result.update(changes)
    return result


def save_session(**changes):
    session = dict(subject="owner", client_id="oaiapp_ARIA", ext_agent_host_id="urn:uuid:host", access_token="ARIA-access",
                   refresh_token="ARIA-refresh", id_token="id", plan_only_confirmed=True, scopes=auth.SCOPES.split(), expires_at=time.time()+3600)
    session.update(changes)
    with auth._locked():
        auth._write("session.json", session)
    return session


def test_registration_has_stable_host_pkce_and_fresh_attempt_state(store):
    a=auth.begin("http://127.0.0.1:14999/auth/callback")
    b=auth.begin("http://127.0.0.1:15000/auth/callback")
    params={k:v[0] for k,v in parse_qs(urlsplit(a["url"]).query).items()}
    assert a["host_id"] == b["host_id"]
    assert a["state"] != b["state"] and a["nonce"] != b["nonce"]
    assert params["agent_name_hint"] == "ARIA" and params["client_id"] == "dynamic_agent_client"
    assert params["code_challenge"] == base64.urlsafe_b64encode(hashlib.sha256(a["verifier"].encode()).digest()).decode().rstrip("=")
    assert "code_verifier" not in params and params["resource"] == auth.RESOURCE


@pytest.mark.parametrize("case",["state","expired","denied","missing_client","missing_code"])
def test_callback_rejects_before_token_exchange(store,monkeypatch,case):
    p=auth.begin("http://127.0.0.1:14999/auth/callback")
    query=dict(state=p["state"], code="one-use", client_id="oaiapp_ARIA")
    if case=="state": query["state"]="wrong"
    if case=="expired":p["deadline"]=0
    if case=="denied":query["error"]="access_denied"
    if case=="missing_client":query.pop("client_id")
    if case=="missing_code":query.pop("code")
    monkeypatch.setattr(auth,"_json_request",lambda *a:pytest.fail("must not exchange"))
    with pytest.raises(ProviderAuthError):auth.finish(p,query)
    assert not (store / "session.json").exists()


def test_issued_client_exchange_scope_and_atomic_private_storage(store,monkeypatch):
    p=auth.begin("http://127.0.0.1:14999/auth/callback")
    requests=[]
    monkeypatch.setattr(auth,"_json_request",lambda url,fields:requests.append((url,fields)) or tokens())
    monkeypatch.setattr(auth,"_validate_id",lambda t,c,n:{"sub":"owner"})
    query=dict(state=p["state"],code="one-use",client_id="oaiapp_ARIA")
    auth.finish(p,query)
    s=auth._read("session.json")
    assert requests[0][1]["client_id"] == "oaiapp_ARIA"
    assert requests[0][1]["redirect_uri"] == p["redirect_uri"]
    assert requests[0][1]["code_verifier"] == p["verifier"]
    assert s["access_token"]=="ARIA-access"
    assert s["plan_only_confirmed"] is False
    with pytest.raises(ProviderAuthError, match="disable ARIA credits"):
        auth.access_token()
    assert (store.stat().st_mode&0o777)==0o700
    assert ((store/"session.json").stat().st_mode&0o777)==0o600
    with pytest.raises(ProviderAuthError):auth.finish(p,query)


@pytest.mark.parametrize("change",[{"scope":"openid"},{"refresh_token":""},{"token_type":"Basic"}])
def test_incomplete_permission_never_overwrites_connection(store,monkeypatch,change):
    old=save_session()
    monkeypatch.setattr(auth,"_validate_id",lambda *a:{"sub":"owner"})
    with pytest.raises(ProviderAuthError):auth._session(tokens(**change),client_id="oaiapp_ARIA",host_id="host",nonce="nonce",previous=old)
    assert auth._read("session.json")==old


@pytest.mark.parametrize("bad",["nonce","issuer","audience","expired","signature"])
def test_real_signed_id_token_validation_rejects_invalid_identity(monkeypatch,bad):
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key()));jwk["kid"]="test"
    discovery={"issuer":auth.ISSUER,"jwks_uri":auth.ISSUER+"/.well-known/jwks.json"}
    monkeypatch.setattr(auth,"_json_request",lambda url:discovery if "openid-configuration" in url else {"keys":[jwk]})
    claims=dict(iss=auth.ISSUER,aud="oaiapp_ARIA",sub="owner",exp=time.time()+300,nonce="nonce")
    good=jwt.encode(claims,key,algorithm="RS256",headers={"kid":"test"})
    assert auth._validate_id(good,"oaiapp_ARIA","nonce")["sub"]=="owner"
    signing=key
    if bad=="nonce":claims["nonce"]="wrong"
    if bad=="issuer":claims["iss"]="https://other.example"
    if bad=="audience":claims["aud"]="other-client"
    if bad=="expired":claims["exp"]=time.time()-60
    if bad=="signature":signing=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    encoded=jwt.encode(claims,signing,algorithm="RS256",headers={"kid":"test"})
    with pytest.raises(ProviderAuthError):auth._validate_id(encoded,"oaiapp_ARIA","nonce")


def test_refresh_serialized_and_rotated_across_concurrent_callers(store,monkeypatch):
    save_session(expires_at=0)
    exchanges=[]
    monkeypatch.setattr(auth,"_validate_id",lambda *a:{"sub":"owner"})
    def refresh(url,fields):
        exchanges.append(fields)
        time.sleep(.02)
        return tokens(access_token="new-access",refresh_token="new-refresh")
    monkeypatch.setattr(auth,"_json_request",refresh)
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert list(pool.map(lambda _:auth.access_token(),range(6))) == ["new-access"]*6
    assert len(exchanges)==1
    assert exchanges[0]["client_id"]=="oaiapp_ARIA" and "scope" not in exchanges[0]
    assert auth._read("session.json")["refresh_token"]=="new-refresh"


def test_owner_lock_insecure_permissions_and_failed_refresh_fail_closed(store,monkeypatch):
    save_session(expires_at=0)
    monkeypatch.setattr(auth,"_json_request",lambda *a:(_ for _ in ()).throw(ProviderAuthError("relogin")))
    with pytest.raises(ProviderAuthError):auth.access_token()
    assert auth._read("session.json")["refresh_token"]=="ARIA-refresh"
    os.chmod(store/"session.json",0o644)
    with pytest.raises(ProviderAuthError):auth.access_token()
    def locked():raise ProviderAuthError("locked")
    monkeypatch.setattr(auth,"_owner_check",locked)
    with pytest.raises(ProviderAuthError,match="locked"):auth.access_token()


@pytest.mark.parametrize("stream",[False,True])
def test_subscription_responses_uses_plan_bearer_sse_and_public_endpoint(fake,monkeypatch,stream):
    monkeypatch.setenv("JARVIS_OPENAI_AUTH_MODE","chatgpt_plan")
    monkeypatch.setattr(auth,"access_token",lambda:"ARIA-plan-access")
    monkeypatch.setattr(auth,"status",lambda:{"state":"credentials_present","source":"aria_oauth"})
    allow("openai",price=(0,0))
    fake.add(FakeResponse(lines=sse(("response.output_text.delta",{"delta":"plan answer"}),
                                  ("response.completed",{"response":openai_completed("plan answer")}))))
    text="".join(gateway.stream_chat(GPT,MSG)) if stream else gateway.chat_with_usage(GPT,MSG)[0]
    assert text=="plan answer"
    req=fake.requests[0]
    assert req["url"]=="https://api.openai.com/v1/responses"
    assert req["headers"]["Authorization"]=="Bearer ARIA-plan-access"
    assert req["body"]["stream"] is True and req["body"]["store"] is False
    assert "max_output_tokens" not in req["body"] and "temperature" not in req["body"]
    assert providers.status()["openai"]["billing"]=="chatgpt_subscription"


def test_subscription_failure_falls_back_local_never_api_key(fake,monkeypatch):
    monkeypatch.setenv("JARVIS_OPENAI_AUTH_MODE","chatgpt_plan")
    monkeypatch.setattr(auth,"status",lambda:{"state":"credentials_present"})
    def denied():raise ProviderAuthError("consent missing")
    monkeypatch.setattr(auth,"access_token",denied)
    allow("openai",price=(0,0))
    with local_answer():assert gateway.chat_with_usage(GPT,MSG)[0]=="local answer"
    assert fake.requests==[]


def test_default_api_auth_and_request_are_preserved(fake,monkeypatch):
    monkeypatch.delenv("JARVIS_OPENAI_AUTH_MODE",raising=False)
    adapter=OpenAIResponses()
    assert adapter.credential()==KEYS["openai_api_key"] and adapter.billing=="api"
    body=adapter._body(Request(model="original",messages=MSG,max_output_tokens=123,temperature=.4),stream=False)
    assert body["max_output_tokens"]==123 and body["temperature"]==.4 and body["stream"] is False


def test_plan_model_catalog_and_namespaced_tools(fake,monkeypatch):
    monkeypatch.setenv("JARVIS_OPENAI_AUTH_MODE","chatgpt_plan")
    monkeypatch.setattr(auth,"access_token",lambda:"ARIA-plan-access")
    fake.add(FakeResponse({"models":[{"slug":"included","display_name":"Included","visibility":"list"},{"slug":"hidden","visibility":"hidden"}]}))
    adapter=OpenAIResponses()
    assert [m.id for m in adapter.discover()]==["included"]
    req=Request(model="included",messages=MSG,tools=[{"function":{"name":"local_tool","parameters":{"type":"object"}}}])
    assert adapter._body(req,stream=False)["tools"][0]["type"]=="namespace"


def test_oauth_tokens_cannot_enter_cloud_disclosure(store):
    from jarvis.inference import cloud_policy
    save_session(access_token="secret-ARIA-oauth-access",refresh_token="secret-ARIA-oauth-refresh",id_token="secret-ARIA-id-token")
    for secret in auth.sensitive_values():
        with pytest.raises(cloud_policy.PolicyRefused):
            cloud_policy.prepare_messages([{"role":"user","content":secret}],["current_turn"])
