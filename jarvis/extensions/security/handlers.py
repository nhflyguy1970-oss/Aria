"""Security extension handlers."""

from jarvis.handlers.registry import register_action
from jarvis.response import ok


@register_action("security_status", info=True, module="security", description="Security status")
def security_status(assistant, params: dict, message: str) -> dict:
    return ok("Security extension loaded — PIN/face modules recovering.", module="security")
