"""Free-tier enforcement uses mock transports, zero spending, and private state."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from jarvis.config import DATA_DIR
from jarvis.inference import cloud_policy, gateway, providers
from jarvis.inference.providers import base
from jarvis.inference.providers.gemini import FREE_TEXT_MODELS
from test_phase4_providers import fake, FakeResponse, gemini_response, sse, KEYS, MSG, local_answer


@pytest.fixture
def free(fake, monkeypatch):
    monkeypatch.setenv("JARVIS_GEMINI_FREE_TIER_ONLY", "1")
    monkeypatch.setenv("JARVIS_CLOUD_PROVIDERS", "google")
    proof={"tier":"Free","project_id":"gen-lang-client-0469537535","owner_confirmed":True,
           "key_sha256":hashlib.sha256(KEYS['gemini_api_key'].encode()).hexdigest()}
    (DATA_DIR/'gemini_free_tier.json').write_text(json.dumps(proof))
    aid=cloud_policy.create_authorization("google",max_cost_usd=0)
    return fake,aid


@pytest.mark.parametrize('stream',[False,True])
@pytest.mark.parametrize('model',sorted(FREE_TEXT_MODELS))
def test_free_models_work_with_zero_budget_and_zero_cost_grant(free,stream,model):
    fake,aid=free
    payload=gemini_response()
    if stream:fake.add(FakeResponse(lines=sse(('',payload))))
    else:fake.add(FakeResponse(payload))
    result=''.join(gateway.stream_chat('google/'+model,MSG)) if stream else gateway.chat_with_usage('google/'+model,MSG)[0]
    assert result=='A dry fly floats.'
    assert cloud_policy.monthly_spend()==0
    assert cloud_policy.load_budget()['monthly_total_usd']==0
    assert cloud_policy.active_authorization('google','general')['max_cost_usd']==0
    assert cloud_policy.usage_rows()[0]['billing']=='gemini_free_tier'


def test_paid_models_unknown_aliases_and_other_providers_remain_blocked(free):
    fake,_=free
    for model in ['gemini-3.1-pro-preview','gemini-flash-latest','unknown']:
        with local_answer():assert gateway.chat_with_usage('google/'+model,MSG)[0]=='local answer'
    with local_answer():assert gateway.chat_with_usage('openai/gpt-test-model',MSG)[0]=='local answer'
    assert fake.requests==[]


def test_rotated_key_or_unverified_tier_is_held(free):
    fake,_=free
    proof=json.loads((DATA_DIR/'gemini_free_tier.json').read_text());proof['key_sha256']='not-the-verified-key'
    (DATA_DIR/'gemini_free_tier.json').write_text(json.dumps(proof))
    with local_answer():assert gateway.chat_with_usage('google/gemini-3.5-flash-lite',MSG)[0]=='local answer'
    assert fake.requests==[]


def test_paid_addons_refused_before_transport(free):
    fake,_=free
    adapter=providers.adapter_for('google')
    for body in [{'tools':[{'googleSearch':{}}]}, {'cachedContent':'cache'}, {'generationConfig':{'responseModalities':['IMAGE']}}]:
        with pytest.raises(base.ProviderAuthError):adapter._send('POST','/x',model='gemini-3.5-flash-lite',body=body)
    assert fake.requests==[]


def test_zero_cost_grant_cannot_authorize_paid_api(free,monkeypatch):
    with pytest.raises(ValueError):cloud_policy.create_authorization('openai',max_cost_usd=0)
    monkeypatch.setenv('JARVIS_GEMINI_FREE_TIER_ONLY','0')
    assert cloud_policy.active_authorization('google','general') is None


def test_concurrent_free_reservations_keep_spend_zero(free):
    def reserve(_):
        r=cloud_policy.preflight('google','google/gemini-3.5-flash-lite','general',input_tokens=20,max_output_tokens=100)
        return cloud_policy.record_usage(r,receipt_id=r.id,status='completed',input_tokens=20,output_tokens=10)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(reserve,range(16)))==[0]*16
    assert cloud_policy.monthly_spend()==0
