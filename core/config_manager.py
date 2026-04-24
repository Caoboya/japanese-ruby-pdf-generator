# -*- coding: utf-8 -*-

import json
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "body_font_size": "15px",
    "ruby_font_size": "0.48em",
    "line_height": "2.0",
    "body_margin": "40px",
    "page_margin": "2cm",
}


def load_config() -> dict:
    path = Path(CONFIG_FILE)

    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()

    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    try:
        Path(CONFIG_FILE).write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass