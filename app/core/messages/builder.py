"""Utility helpers for message keys."""


def build_message_key(module: str, action: str) -> str:
    return f"{module}.{action}"
