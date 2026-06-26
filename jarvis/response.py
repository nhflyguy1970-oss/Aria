# Source Generated with Decompyle++
# File: response.cpython-312.pyc (Python 3.12)

'''Standard assistant response payloads.'''
import re
_MAX_STREAM_DIFF = 48000
_MAX_STREAM_DIFF_LINES = 180

def ok(message = None, module = None, **extra):
    pass
# WARNING: Decompyle incomplete


def err(message = None, module = None, **extra):
    pass
# WARNING: Decompyle incomplete


def _trim_proposal_message(message = None):
    '''Drop embedded code fences when the UI renders a separate diff block.'''
    if not message:
        message
    text = re.sub('```[\\s\\S]*?```', '', '').strip()
    text = re.sub('\\n{3,}', '\n\n', text)
    return text


def cap_stream_payload(result = None, *, lite_ui):
    '''Keep SSE payloads small enough for WebKit/pywebview chat UI.'''
    payload = dict(result)
    if payload.get('proposal_id') and payload.get('message'):
        payload['message'] = _trim_proposal_message(str(payload['message']))
    if lite_ui and payload.get('proposal_id'):
        payload.pop('diff', None)
        payload['diff_omitted'] = True
        return payload
    diff = None.get('diff')
    if isinstance(diff, str) and diff:
        lines = diff.splitlines()
        if len(lines) > _MAX_STREAM_DIFF_LINES:
            payload['diff'] = '\n'.join(lines[:_MAX_STREAM_DIFF_LINES])
            payload['diff_truncated'] = True
            payload['diff_total_lines'] = len(lines)
            return payload
        if None(diff) > _MAX_STREAM_DIFF:
            payload['diff'] = diff[:_MAX_STREAM_DIFF]
            payload['diff_truncated'] = True
            payload['diff_total_lines'] = len(lines)
    return payload


def stream_done(result = None, *, lite_ui):
    payload = cap_stream_payload(dict(result), lite_ui = lite_ui)
    if payload.get('type') and payload['type'] != 'done':
        payload['result_type'] = payload['type']
    payload['type'] = 'done'
    return payload

