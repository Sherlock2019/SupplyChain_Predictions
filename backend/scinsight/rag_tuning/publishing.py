"""Controlled publication: validate -> sync the Flowise chatflow RAG DB -> switch the active pointer. Rollback re-activates a
previously published version the same way. On any failure the current configuration stays active."""
from __future__ import annotations

import json
from pathlib import Path

from backend.scinsight.db import now_iso
from backend.scinsight.rag_tuning.config import RagTuningConfig
from backend.scinsight.rag_tuning.evaluation import compare_experiments
from backend.scinsight.rag_tuning.indexing import validate_index


def validate_config(registry, kb, flowise, knowledge_dir: Path, tenant_id: str, config_id: str, dataset_version: str = "v1",
                    require_benchmark: bool = True) -> dict:
    """Every check a configuration must pass before it can become active."""
    row = registry.get(tenant_id, config_id)
    cfg = RagTuningConfig.model_validate(row["config"])
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
    check("status", row["status"] in ("candidate", "retired"), f"status is {row['status']} (needs a built candidate index, or a previously published version)")
    if row["index_version"]:
        report = validate_index(kb, knowledge_dir, tenant_id, row["index_version"], cfg)
        check("index", report["ok"], "; ".join(report["problems"]) or f"{report['documents']} documents, {report['chunks']} chunks, dims {report['dims']}")
    else:
        check("index", False, "no index built yet")
    try:
        kb.embedder_for(cfg.embedding_model)
        check("embedding_model", True, f"{cfg.embedding_model} loads")
    except Exception as exc:  # noqa: BLE001
        check("embedding_model", False, str(exc))
    if flowise is not None and flowise.configured:
        problems = flowise.compatible(cfg)
        check("flowise_compatible", not problems, "; ".join(problems) or "the chatflow RAG DB can mirror chunk size, overlap and top-k")
    if require_benchmark:
        active = registry.get_active_rag_config(tenant_id)
        mine = [e for e in registry.experiments(tenant_id, config_id) if e["dataset_version"] == dataset_version]
        theirs = [e for e in registry.experiments(tenant_id, active["id"]) if e["dataset_version"] == dataset_version]
        if not mine:
            check("benchmark", False, f"no benchmark of {config_id} on dataset {dataset_version}")
        elif not theirs:
            check("benchmark", False, f"no benchmark of the active configuration {active['id']} on dataset {dataset_version} to compare with")
        else:
            cmp = compare_experiments({**theirs[0], "dataset_version": dataset_version}, {**mine[0], "dataset_version": dataset_version})
            check("benchmark", cmp["passed"], cmp["recommendation"])
    ok = all(c["ok"] for c in checks)
    registry.set_status(config_id, row["status"], validation={"ok": ok, "checks": checks, "at": now_iso()})
    return {"config_id": config_id, "ok": ok, "checks": checks}


def _activate(registry, kb, flowise, tenant_id: str, config_id: str, user_id: str, action: str) -> dict:
    row = registry.get(tenant_id, config_id)
    cfg = RagTuningConfig.model_validate(row["config"])
    previous = registry.get_active_rag_config(tenant_id)
    sync, previous_flow = {"skipped": "Flowise not configured for the SCInsight API"}, None
    # 1. the chatflow RAG DB first: if it fails it is restored and nothing else changes.
    #    flowise_backup of a version = the exact chatflow it ran with, so a rollback restores it rather than re-deriving it.
    if flowise is not None and flowise.configured:
        saved = kb.db.one("select flowise_backup from rag_config_versions where id=?", (config_id,))["flowise_backup"]
        if action == "rollback" and saved:
            previous_flow = flowise.chatflow()["flowData"]
            sync = flowise.restore(saved)
        else:
            sync = flowise.sync(cfg, config_id)
            previous_flow = sync.pop("backup")
    # 2. switch the active pointer in one transaction (live search reads it on the next query)
    kb.db.transaction([
        ("update rag_config_versions set flowise_backup=coalesce(flowise_backup, ?) where id=?", (previous_flow, previous["id"])),
        ("update rag_config_versions set status='retired' where tenant_id=? and status='active'", (tenant_id,)),
        ("update rag_config_versions set status='active', published_by=?, published_at=?, flowise_sync=? where tenant_id=? and id=?",
         (user_id, now_iso(), json.dumps(sync), tenant_id, config_id)),
    ])
    return {"action": action, "active": config_id, "previous": previous["id"], "index_version": row["index_version"], "flowise": sync}


def publish_rag_config(registry, kb, flowise, knowledge_dir: Path, tenant_id: str, config_id: str, user_id: str, dataset_version: str = "v1") -> dict:
    report = validate_config(registry, kb, flowise, knowledge_dir, tenant_id, config_id, dataset_version)
    if not report["ok"]:
        raise ValueError("publish refused: " + "; ".join(f"{c['check']}: {c['detail']}" for c in report["checks"] if not c["ok"]))
    if registry.get(tenant_id, config_id)["status"] != "candidate":
        raise ValueError("publish takes a candidate; use rollback to re-activate an earlier version")
    return {**_activate(registry, kb, flowise, tenant_id, config_id, user_id, "publish"), "validation": report}


def rollback_rag_config(registry, kb, flowise, knowledge_dir: Path, tenant_id: str, config_id: str, user_id: str) -> dict:
    """Re-activate a version that was published before (its index is kept); refused if that index is stale or incomplete."""
    row = registry.get(tenant_id, config_id)
    if row["status"] != "retired" or not row["published_at"]:
        raise ValueError(f"{config_id} was never published: only previously active versions can be rolled back to")
    report = validate_config(registry, kb, flowise, knowledge_dir, tenant_id, config_id, require_benchmark=False)
    if not report["ok"]:
        raise ValueError("rollback refused: " + "; ".join(f"{c['check']}: {c['detail']}" for c in report["checks"] if not c["ok"]))
    return {**_activate(registry, kb, flowise, tenant_id, config_id, user_id, "rollback"), "validation": report}
