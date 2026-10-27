"""Backend-approved embedding models. The console can only pick from this list: a model id typed in the browser never
reaches a model loader. A model that is not installed is reported as unavailable, never replaced by another model.
"""
from __future__ import annotations

import math
import os
import time
from pathlib import Path

# id -> facts shown in the console. "installed" is checked at runtime (fastembed cache), never assumed.
FASTEMBED_MODELS = {
    "BAAI/bge-small-en-v1.5": {"provider": "fastembed (ONNX, CPU)", "dims": 384, "languages": "English",
                               "role": "current model (baked into the image; also serves the gateway /v1/embeddings used by Flowise)",
                               "cache_dir": "models--Qdrant--bge-small-en-v1.5-onnx-Q", "size_mb": 67},
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
        "provider": "fastembed (ONNX, CPU)", "dims": 384, "languages": "50+ languages (multilingual candidate)",
        "role": "multilingual candidate: same 384 dimensions, different embedding space (needs its own index)",
        "cache_dir": "models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q", "size_mb": 220},
    "BAAI/bge-base-en-v1.5": {"provider": "fastembed (ONNX, CPU)", "dims": 768, "languages": "English",
                              "role": "larger English candidate (no supply-chain-specific embedding model is installed or approved)",
                              "cache_dir": "models--qdrant--bge-base-en-v1.5-onnx-Q", "size_mb": 210},
}
HASH_MODELS = {  # offline / test backend: deterministic bag-of-words hashing, not a semantic model
    "hash-bow-384": {"provider": "hash (tests)", "dims": 384, "languages": "token hashing", "role": "offline test embedder"},
    "hash-bow-128": {"provider": "hash (tests)", "dims": 128, "languages": "token hashing", "role": "offline test embedder (other dimension)"},
}


class ModelUnavailable(RuntimeError):
    pass


def approved(backend: str) -> dict[str, dict]:
    return HASH_MODELS if backend == "hash" else FASTEMBED_MODELS


def _installed(model: str, backend: str) -> bool:
    if backend == "hash":
        return True
    # fastembed stores each model as models--<org>--<name>[-onnx...]; match on the model name, whatever the hosting org
    cache = Path(os.environ.get("FASTEMBED_CACHE_PATH", "/opt/fastembed"))
    short = model.split("/")[-1].lower()
    return cache.exists() and any(short in p.name.lower() and any(p.rglob("*.onnx")) for p in cache.glob("models--*"))


def list_supported_embedding_models(backend: str, active_model: str) -> list[dict]:
    """The approved list with what is actually known about each model (installed, dimensions, languages)."""
    return [{"id": mid, **{k: v for k, v in meta.items() if k != "cache_dir"}, "installed": _installed(mid, backend),
             "active": mid == active_model} for mid, meta in approved(backend).items()]


_cache: dict[str, object] = {}


def get_embedder(model: str, backend: str, allow_download: bool = False):
    """Embedder for an approved model. Raises ModelUnavailable instead of substituting a different model."""
    models = approved(backend)
    if model not in models:
        raise ModelUnavailable(f"{model} is not an approved embedding model for the {backend} backend")
    if model in _cache:
        return _cache[model]
    if backend == "hash":
        from backend.scinsight.rag import HashEmbedder
        emb = HashEmbedder(dims=models[model]["dims"], name=model)
    else:
        if not allow_download and not _installed(model, backend):
            raise ModelUnavailable(f"{model} is not installed in this image (cache {os.environ.get('FASTEMBED_CACHE_PATH', '/opt/fastembed')}); "
                                   "use 'Test model loading' to download it (needs internet), or bake it into the image")
        from backend.app.rag import get_embedder as gateway_embedder  # same FastEmbedder class as the live RAG
        try:
            emb = gateway_embedder("fastembed", model)
            emb.embed(["warm-up"])
        except Exception as exc:  # noqa: BLE001 - surface any loader error to the console as "unavailable"
            raise ModelUnavailable(f"{model} could not be loaded: {str(exc)[:300]}") from exc
    _cache[model] = emb
    return emb


def test_model(model: str, backend: str, samples: list[str]) -> dict:
    """Load the model (downloading it if allowed), embed sample texts, check dimensions and measure latency."""
    t0 = time.perf_counter()
    emb = get_embedder(model, backend, allow_download=True)
    load_ms = (time.perf_counter() - t0) * 1000
    t1 = time.perf_counter()
    vectors = emb.embed(samples)
    embed_ms = (time.perf_counter() - t1) * 1000
    dims = {len(v) for v in vectors}
    expected = approved(backend)[model]["dims"]
    norms = [round(math.sqrt(sum(x * x for x in v)), 4) for v in vectors]
    return {"model": model, "loaded": True, "load_ms": round(load_ms, 1), "embed_ms_total": round(embed_ms, 1),
            "embed_ms_per_text": round(embed_ms / max(1, len(samples)), 2), "dims": sorted(dims), "expected_dims": expected,
            "dims_ok": dims == {expected}, "norms": norms, "sample_head": [[round(x, 4) for x in v[:6]] for v in vectors[:2]]}
