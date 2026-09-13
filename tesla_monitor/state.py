"""Persistência simples do conjunto de veículos já vistos entre execuções."""
import json
import os


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {"seen_ids": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: str, state: dict) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)
