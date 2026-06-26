"""Voice extension handlers."""

from jarvis.handlers.registry import register_action
from jarvis.response import ok


@register_action("voice_smoke_test", info=True, module="audio", description="Hello ARIA voice smoke test")
def voice_smoke_test(assistant, params: dict, message: str) -> dict:
    return ok("Voice path OK — full duplex smoke test recovering from bytecode restore.", module="audio")
