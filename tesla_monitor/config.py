"""Carregamento de configuração (YAML) com substituição de variáveis de ambiente."""
import os
import re

import yaml

_ENV_PATTERN = re.compile(r"\$\{([^}^{]+)\}")


def _resolve_env(value):
    if isinstance(value, str):
        def repl(match):
            return os.environ.get(match.group(1), "")

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return _resolve_env(raw)
