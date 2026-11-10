"""Text preprocessing: URL and user placeholders, hashtags kept or removed."""
from __future__ import annotations

import re
from dataclasses import dataclass

HASHTAG_MODES = ("keep", "remove")

_URL_RE = re.compile(r"(?:https?://|www\.)[!-~]+", re.IGNORECASE)
_USER_RE = re.compile(r"(?<![\w@])@[^\s@]+")
_HASHTAG_RE = re.compile(r"#[^\s#]+")
_WS_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class PreprocOpts:
    url_token: str = "<URL>"
    user_token: str = "<USER>"
    collapse_whitespace: bool = True

    @classmethod
    def from_config(cls, cfg: dict) -> "PreprocOpts":
        return cls(**cfg["modelling"]["preprocess"])

    @property
    def placeholders(self) -> tuple[str, ...]:
        return (self.url_token, self.user_token)


def validate_mode(hashtag_mode: str | None) -> str:
    """Return the hashtag mode, or raise ValueError for an unknown one."""
    if hashtag_mode not in HASHTAG_MODES:
        raise ValueError(f"hashtag_mode must be one of {HASHTAG_MODES}; got {hashtag_mode!r}")
    return hashtag_mode


def preprocess(text: str, hashtag_mode: str, opts: PreprocOpts = PreprocOpts()) -> str:
    mode = validate_mode(hashtag_mode)
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    t = _URL_RE.sub(opts.url_token, text)
    t = _USER_RE.sub(opts.user_token, t)
    if mode == "remove":
        t = _HASHTAG_RE.sub("", t)
    if opts.collapse_whitespace:
        t = _WS_RE.sub(" ", t).strip()
    return t


def has_hashtag(text: str) -> bool:
    """True if the raw text contains a hashtag (URLs are ignored)."""
    return _HASHTAG_RE.search(_URL_RE.sub(" ", text)) is not None


def hashtag_modes(cfg: dict) -> list[str]:
    """The hashtag modes in config order."""
    return [validate_mode(m) for m in cfg["modelling"]["hashtag_modes"]]
