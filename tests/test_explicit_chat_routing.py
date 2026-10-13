"""Explicit chat selections across the real engine/gateway; no live providers."""
import hashlib
import json
from unittest.mock import patch

import pytest

from test_phase4_providers import fake as fake, FakeResponse, gemini_response, http_error, sse
from jarvis.inference import boundary, cloud_policy, gateway, providers

GEMINI = 'google/gemini-3.5-flash-lite'
LOCAL = 'qwen2.5:7b'
MESSAGE = [{'role': 'user', 'content': 'A short greeting about a cedar tree, please.'}]


@pytest.fixture
def free_tier(fake, monkeypatch, data_dir):
    monkeypatch.setenv('JARVIS_GEMINI_FREE_TIER_ONLY', '1')
    monkeypatch.setenv('JARVIS_CLOUD_PROVIDERS', 'google')
    (data_dir / 'gemini_free_tier.json').write_text(json.dumps({
        'tier': 'Free', 'project_id': 'test-free', 'owner_confirmed': True,
        'key_sha256': hashlib.sha256(b'AIzaTEST0123456789abcdefghij').hexdigest(),
    }))
    monkeypatch.setattr('jarvis.inference.execution_policy.apply_policy_to_route',
        lambda **kw: {'model': LOCAL, 'hardware': 'cpu', 'source': 'user_config'})
    cloud_policy.create_authorization('google', max_cost_usd=0, context_classes=['current_turn'])
    return fake


def call(stream, messages=MESSAGE, model=GEMINI, explicit=True):
    if stream:
        return ''.join(gateway.stream_chat(model, messages, explicit_model=explicit))
    return gateway.chat_with_usage(model, messages, explicit_model=explicit)[0]


def response(fake, stream):
    if stream:
        fake.add(FakeResponse(lines=sse(('', gemini_response('Cloud greeting.')))))
    else:
        fake.add(FakeResponse(gemini_response('Cloud greeting.')))


@pytest.mark.parametrize('stream', [False, True])
def test_selected_gemini_survives_saved_local_policy_at_zero_cost(free_tier, stream):
    response(free_tier, stream)
    with patch.object(gateway, '_ollama_chat_with_usage') as local, patch.object(gateway, '_ollama_stream') as local_stream:
        assert call(stream) == 'Cloud greeting.'
    local.assert_not_called(); local_stream.assert_not_called()
    receipt = boundary.recent_receipts(1)[0]
    assert receipt['executed_provider'] == 'google' and not receipt['fallback_used']
    assert cloud_policy.monthly_spend() == 0
    assert all(row['billing'] == 'gemini_free_tier' for row in cloud_policy.usage_rows())


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('failure', ['disabled', 'offline', 'allowlist', 'credentials', 'authorization', 'paid_model', 'private'])
def test_selected_cloud_refusal_never_executes_local_or_transmits(free_tier, monkeypatch, stream, failure):
    messages = MESSAGE
    model = GEMINI
    if failure == 'disabled': monkeypatch.setenv('JARVIS_CLOUD_INFERENCE', '0')
    if failure == 'offline': monkeypatch.setenv('JARVIS_OFFLINE', '1')
    if failure == 'allowlist': monkeypatch.setenv('JARVIS_CLOUD_PROVIDERS', 'openai')
    if failure == 'credentials': monkeypatch.setattr(providers, 'has_credentials', lambda provider: False)
    if failure == 'authorization':
        for a in cloud_policy.list_authorizations(): cloud_policy.revoke_authorization(a['id'])
    if failure == 'paid_model': model = 'google/gemini-unpriced-paid'
    if failure == 'private': messages = [{'role':'user', 'content':'Health record context (authoritative local PHR: private test'}]
    with patch.object(gateway, '_ollama_chat_with_usage') as local, patch.object(gateway, '_ollama_stream') as local_stream:
        with pytest.raises(boundary.InferenceError): call(stream, messages=messages, model=model)
    local.assert_not_called(); local_stream.assert_not_called()
    assert free_tier.requests == []
    assert boundary.recent_receipts(1)[0]['status'] == 'failed'


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('code', [404, 429, 503])
def test_selected_cloud_failure_never_falls_back(free_tier, stream, code):
    for _ in range(3): free_tier.add(http_error(code))
    with patch.object(gateway, '_ollama_chat_with_usage') as local, patch.object(gateway, '_ollama_stream') as local_stream:
        with pytest.raises(boundary.InferenceError): call(stream)
    local.assert_not_called(); local_stream.assert_not_called()
    receipt = boundary.recent_receipts(1)[0]
    assert receipt['status'] == 'failed' and not receipt['fallback_used']
    assert {a['provider'] for a in receipt['attempts']} == {'google'}


@pytest.mark.parametrize('stream', [False, True])
def test_selected_cloud_withholds_ungranted_system_and_history(free_tier, stream):
    response(free_tier, stream)
    messages = [{'role':'system','content':'PRIVATE SYSTEM'}, {'role':'user','content':'PRIVATE HISTORY'},
                {'role':'assistant','content':'PRIVATE ANSWER'}] + MESSAGE
    call(stream, messages=messages)
    body = json.dumps(free_tier.requests[0]['body'])
    assert all(s not in body for s in ('PRIVATE SYSTEM','PRIVATE HISTORY','PRIVATE ANSWER'))
    assert 'cedar tree' in body


@pytest.mark.parametrize('stream', [False, True])
def test_no_ui_override_keeps_saved_local_default(free_tier, stream):
    with patch.object(gateway, '_ollama_chat_with_usage', return_value=('local', {})) as local, \
         patch.object(gateway, '_ollama_stream', return_value=iter(['local'])) as local_stream:
        assert call(stream, model='router-suggested:7b', explicit=False) == 'local'
    assert free_tier.requests == []
    assert boundary.recent_receipts(1)[0]['executed_model'] == LOCAL


def test_explicit_local_selection_survives_saved_local_default(free_tier):
    with patch.object(gateway, '_ollama_chat_with_usage', return_value=('selected', {})) as local:
        assert call(False, model='other-local:7b') == 'selected'
    assert local.call_args[0][0] == 'other-local:7b'


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('policy_source', ['user_config', 'env'])
def test_real_chat_engine_honors_ui_selection_over_router_model(free_tier, monkeypatch, assistant, stream, policy_source):
    from jarvis.behaviors.conversation import ConversationEngine
    assistant.session.note_chat_model(GEMINI)
    monkeypatch.setattr('jarvis.inference.execution_policy.apply_policy_to_route',
        lambda **kw: {'model':LOCAL, 'hardware':'cpu', 'source':policy_source})
    eng = ConversationEngine(assistant)
    monkeypatch.setattr(eng, 'build_context_prefix', lambda msg: ('PRIVATE ACM', [], []))
    monkeypatch.setattr(eng, 'try_strict_instructions', lambda msg: None)
    monkeypatch.setattr(eng, '_apply_answer_integrity_gates', lambda msg, answer, **kw: answer)
    monkeypatch.setattr(eng, 'auto_remember', lambda *a: None)
    monkeypatch.setattr(eng, '_learn_preferences', lambda *a: None)
    response(free_tier, stream)
    with patch('jarvis.behaviors.conversation.check_ollama', side_effect=AssertionError('local preflight')):
        if stream:
            result = list(eng.execute_stream('A short greeting about a cedar tree, please.', {'model':LOCAL, 'knowledge_mode':True}))[-1]
        else:
            result = eng.execute({'model':LOCAL, 'knowledge_mode':True}, 'A short greeting about a cedar tree, please.')
    assert result['ok'], result
    assert result['receipt']['executed_provider'] == 'google' and result['model'] == GEMINI
    assert 'PRIVATE ACM' not in json.dumps(free_tier.requests[0]['body'])


@pytest.mark.parametrize('stream', [False, True])
def test_real_chat_engine_reports_unauthorized_selected_provider(free_tier, monkeypatch, assistant, stream):
    from jarvis.behaviors.conversation import ConversationEngine
    assistant.session.note_chat_model(GEMINI)
    eng = ConversationEngine(assistant)
    monkeypatch.setattr(eng, 'build_context_prefix', lambda msg: ('', [], []))
    monkeypatch.setattr(eng, 'try_strict_instructions', lambda msg: None)
    monkeypatch.setenv('JARVIS_CLOUD_INFERENCE', '0')
    with patch('jarvis.behaviors.conversation.check_ollama', side_effect=AssertionError('local preflight')):
        result = list(eng.execute_stream('A greeting, please.', {'model':LOCAL}))[-1] if stream else eng.execute({'model':LOCAL}, 'A greeting, please.')
    assert result['ok'] is False
    assert 'Selected Gemini' in result['message'] and 'No local fallback' in result['message']
    assert 'local model service' not in result['message']
    assert free_tier.requests == []


@pytest.mark.parametrize('selection,router_model,expected_warm', [
    (GEMINI, LOCAL, []),
    ('', GEMINI, []),
    ('selected-local:7b', LOCAL, ['selected-local:7b']),
    ('', 'router-default:7b', [LOCAL]),
])
def test_http_stream_preflight_respects_selection(monkeypatch, selection, router_model, expected_warm):
    """Exercise the real HTTP/SSE entry point without inference or a server lifespan."""
    import asyncio
    from types import SimpleNamespace
    from jarvis.gui import server

    warmed = []
    dispatched = []

    def ensure(model, **kwargs):
        warmed.append(model)
        return {'ok': True, 'model': model, 'action': 'already_ready'}

    def process_stream(message, attachment, **kwargs):
        dispatched.append(kwargs)
        yield {'type': 'token', 'token': 'ok'}
        yield {'type': 'done', 'ok': True, 'message': 'ok'}

    monkeypatch.setattr(server, 'assistant', SimpleNamespace(
        session=SimpleNamespace(chat_model=selection),
        branches=SimpleNamespace(active_id='test'), process_stream=process_stream))
    monkeypatch.setattr('jarvis.llm.general_model', lambda: LOCAL)
    monkeypatch.setattr('jarvis.router.route', lambda *a: {'action':'chat','params':{'model':router_model}})
    monkeypatch.setattr('jarvis.ollama_runtime.ensure_chat_model_ready', ensure)

    async def run():
        result = await server.chat(message='A short greeting, please.', file=None, file2=None,
            stream='true', branch_id='', crop='', video_second='', pdf_page='',
            request_id='http-selection-test', lite_ui='true', preferred_module='')
        return [event async for event in result.body_iterator]

    events = asyncio.run(run())
    assert any('"ok": true' in event for event in events), events
    assert warmed == expected_warm
    assert len(dispatched) == 1
    assert dispatched[0]['intent']['params']['model'] == router_model
