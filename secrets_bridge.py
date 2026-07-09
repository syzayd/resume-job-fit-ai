"""Bridges Streamlit Community Cloud secrets into os.environ.

Cloud stores secrets in st.secrets; locally there is no secrets.toml, and
reading st.secrets (via `in` or `[]`) raises StreamlitSecretNotFoundError.
Local runs use a real .env instead, so a missing secrets.toml is expected there.
"""

import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def load_secrets_into_env(keys):
    try:
        for key in keys:
            if key in st.secrets and not os.environ.get(key):
                os.environ[key] = st.secrets[key]
    except StreamlitSecretNotFoundError:
        return
