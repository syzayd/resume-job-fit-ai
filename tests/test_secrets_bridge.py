"""Unit tests for secrets_bridge.py - no secrets.toml is present in CI or local dev."""

from __future__ import annotations

import os
from unittest.mock import patch

import streamlit as st

from secrets_bridge import load_secrets_into_env


def test_no_secrets_file_does_not_raise(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    # No .streamlit/secrets.toml in this environment, so st.secrets access
    # normally raises StreamlitSecretNotFoundError; this must not propagate.
    load_secrets_into_env(("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    assert "GEMINI_API_KEY" not in os.environ
    assert "GOOGLE_API_KEY" not in os.environ


def test_secret_present_is_copied_into_env(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with patch.object(st, "secrets", {"GEMINI_API_KEY": "cloud-value"}):
        load_secrets_into_env(("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    assert os.environ["GEMINI_API_KEY"] == "cloud-value"


def test_existing_env_var_is_not_overwritten(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "local-value")
    with patch.object(st, "secrets", {"GEMINI_API_KEY": "cloud-value"}):
        load_secrets_into_env(("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    assert os.environ["GEMINI_API_KEY"] == "local-value"
