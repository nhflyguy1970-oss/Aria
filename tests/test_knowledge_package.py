"""Knowledge package exports — learn commands available from jarvis.knowledge."""

from __future__ import annotations


def test_is_learn_command_importable():
    from jarvis.knowledge import is_learn_command, parse_learn_topic

    assert is_learn_command("learn about: Python typing")
    assert parse_learn_topic("learn about: Python typing") == "Python typing"
