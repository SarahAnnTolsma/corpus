"""An Anthropic client after checking that ANTHROPIC_API_KEY is configured."""
from __future__ import annotations

from corpus.config import require_env


def make(*, async_: bool = True, **kwargs):
    """AsyncAnthropic (default) or Anthropic, with the key from the environment
    or .env. Exits with a message naming the missing variable if unset."""
    require_env("ANTHROPIC_API_KEY")
    import anthropic
    return anthropic.AsyncAnthropic(**kwargs) if async_ else anthropic.Anthropic(**kwargs)
