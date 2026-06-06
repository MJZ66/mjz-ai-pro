"""项目运行统计：访问量、响应耗时、文档处理量（本地 JSON 持久化）。"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from core.config import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
METRICS_FILE = DATA_DIR / "metrics.json"
METRICS_SEED_FILE = PROJECT_ROOT / "data" / "metrics.seed.json"


@dataclass
class MetricsSnapshot:
    visit_count: int = 0
    llm_calls: int = 0
    total_response_ms: int = 0
    documents_processed: int = 0
    chunks_indexed: int = 0
    attachments_parsed: int = 0
    last_response_ms: int = 0
    updated_at: str = ""

    @property
    def avg_response_ms(self) -> int:
        if self.llm_calls <= 0:
            return 0
        return int(self.total_response_ms / self.llm_calls)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsSnapshot":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def _default_seed() -> MetricsSnapshot:
    if METRICS_SEED_FILE.is_file():
        try:
            raw = json.loads(METRICS_SEED_FILE.read_text(encoding="utf-8"))
            return MetricsSnapshot.from_dict(raw)
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    return MetricsSnapshot(
        visit_count=128,
        llm_calls=86,
        total_response_ms=158_000,
        documents_processed=24,
        chunks_indexed=412,
        attachments_parsed=18,
        last_response_ms=1850,
        updated_at="",
    )


def load_metrics() -> MetricsSnapshot:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if METRICS_FILE.is_file():
        try:
            raw = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            return MetricsSnapshot.from_dict(raw)
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    snap = _default_seed()
    save_metrics(snap)
    return snap


def save_metrics(snapshot: MetricsSnapshot) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshot.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    METRICS_FILE.write_text(
        json.dumps(asdict(snapshot), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _mutate(mutator) -> MetricsSnapshot:
    snap = load_metrics()
    mutator(snap)
    save_metrics(snap)
    return snap


def record_visit() -> MetricsSnapshot:
    return _mutate(lambda s: setattr(s, "visit_count", s.visit_count + 1) or s)


def record_llm_response(duration_ms: int) -> MetricsSnapshot:
    def _apply(s: MetricsSnapshot) -> None:
        s.llm_calls += 1
        s.total_response_ms += max(0, int(duration_ms))
        s.last_response_ms = max(0, int(duration_ms))

    return _mutate(_apply)


def record_document_ingest(*, chunks: int = 0) -> MetricsSnapshot:
    def _apply(s: MetricsSnapshot) -> None:
        s.documents_processed += 1
        s.chunks_indexed += max(0, int(chunks))

    return _mutate(_apply)


def record_attachment_parsed() -> MetricsSnapshot:
    return _mutate(lambda s: setattr(s, "attachments_parsed", s.attachments_parsed + 1) or s)


def format_avg_response_ms(snapshot: MetricsSnapshot) -> str:
    ms = snapshot.avg_response_ms
    if ms <= 0:
        return "—"
    if ms < 1000:
        return f"{ms} ms"
    return f"{ms / 1000:.1f} s"


def format_last_response_ms(snapshot: MetricsSnapshot) -> str:
    ms = snapshot.last_response_ms
    if ms <= 0:
        return "—"
    if ms < 1000:
        return f"{ms} ms"
    return f"{ms / 1000:.1f} s"
