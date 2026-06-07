from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def read_structured(path: str | Path, default: Any | None = None) -> Any:
    """Read JSON/YAML data with a JSON fallback for minimal environments."""
    file_path = Path(path)
    if not file_path.exists():
        return default

    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        return default

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if yaml is not None:
        return yaml.safe_load(text)

    raise RuntimeError(
        f"Cannot read {file_path}. Install PyYAML, or keep the file in JSON format."
    )


def write_structured(path: str | Path, data: Any) -> None:
    """Write YAML when PyYAML exists, otherwise write pretty JSON."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if yaml is not None:
        text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    else:
        text = json.dumps(data, ensure_ascii=False, indent=2)

    file_path.write_text(text, encoding="utf-8")


def read_json(path: str | Path, default: Any | None = None) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
