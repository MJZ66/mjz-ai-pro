"""metrics 模块测试。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils import metrics  # noqa: E402


def test_load_from_seed_when_no_runtime_file(tmp_path, monkeypatch):
    seed = tmp_path / "metrics.seed.json"
    seed.write_text(
        json.dumps(
            {
                "visit_count": 10,
                "llm_calls": 5,
                "total_response_ms": 5000,
                "documents_processed": 3,
                "chunks_indexed": 30,
                "attachments_parsed": 2,
                "last_response_ms": 900,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(metrics, "METRICS_SEED_FILE", seed)
    monkeypatch.setattr(metrics, "METRICS_FILE", tmp_path / "metrics.json")
    monkeypatch.setattr(metrics, "DATA_DIR", tmp_path)

    snap = metrics.load_metrics()
    assert snap.visit_count == 10
    assert snap.avg_response_ms == 1000


def test_record_visit_and_llm(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "METRICS_FILE", tmp_path / "metrics.json")
    monkeypatch.setattr(metrics, "DATA_DIR", tmp_path)
    monkeypatch.setattr(metrics, "METRICS_SEED_FILE", tmp_path / "missing.json")

    metrics.save_metrics(metrics.MetricsSnapshot())
    metrics.record_visit()
    metrics.record_llm_response(1200)
    snap = metrics.load_metrics()
    assert snap.visit_count == 1
    assert snap.llm_calls == 1
    assert snap.avg_response_ms == 1200


def test_record_document_ingest(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "METRICS_FILE", tmp_path / "metrics.json")
    monkeypatch.setattr(metrics, "DATA_DIR", tmp_path)
    metrics.save_metrics(metrics.MetricsSnapshot())
    metrics.record_document_ingest(chunks=4)
    snap = metrics.load_metrics()
    assert snap.documents_processed == 1
    assert snap.chunks_indexed == 4
