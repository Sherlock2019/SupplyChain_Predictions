from __future__ import annotations

from datetime import date

import pytest

from backend.app.config import ROOT
from backend.app.engine import SupplyChainEngine
from backend.app.sap import SapRepository


@pytest.fixture(scope="module")
def engine() -> SupplyChainEngine:
    return SupplyChainEngine(SapRepository(ROOT / "data" / "sap_mock.json"))


def test_readiness_counts_only_unrestricted_stock_and_confirmed_pos(engine):
    result = engine.factory_readiness("FR10", "FG-PERFUME-100", 8000, date(2026, 10, 30))
    bottles = next(c for c in result["components"] if c["component"] == "PK-BOTTLE-100")
    assert bottles["required"] == 8120  # 8000 * 1.015 rounded up for EA
    assert bottles["unrestricted_on_hand"] == 4100  # 1,800 blocked bottles excluded
    assert bottles["confirmed_inbound_by_need_date"] == 3000  # unconfirmed PO 4500001006 excluded
    assert bottles["shortage"] == 1020
    assert any(row["status"] == "blocked" for row in bottles["excluded_stock"])
    action = next(a for a in result["proposed_actions"] if a["material"] == "PK-BOTTLE-100")
    assert action["action"] == "source_material"
    assert action["approved_secondary_source"] == "Verallia Premium"
    assert result["status"] == "not_ready"  # fragrance and cartons are short too: 1 of 4 components covered
    assert result["component_readiness_pct"] == 25.0


def test_readiness_proposes_expedite_of_later_confirmed_po(engine):
    result = engine.factory_readiness("FR20", "FG-SERUM-50", 6000, date(2026, 10, 27))
    active = next(c for c in result["components"] if c["component"] == "RM-ACTIVE")
    assert active["required"] == pytest.approx(24.72)
    assert active["available"] == 18  # 15 kg in quality inspection is excluded; PO arrives 28 Oct
    expedite = next(a for a in result["proposed_actions"] if a["material"] == "RM-ACTIVE")
    assert expedite["action"] == "expedite_purchase_order"
    assert expedite["purchase_order"] == "4500001002"
    assert expedite["quantity"] == pytest.approx(6.72)


def test_expired_batches_are_excluded(engine):
    result = engine.factory_readiness("TPM1", "FG-CREAM-50", 2800, date(2026, 11, 10))
    base = next(c for c in result["components"] if c["component"] == "RM-BASE")
    assert base["unrestricted_on_hand"] == 380  # BAS-TP-0 expired 2026-10-10
    assert base["excluded_stock"][0]["status"] == "expired"


def test_ready_when_all_components_covered(engine):
    result = engine.factory_readiness("FR10", "FG-PERFUME-100", 3000, date(2026, 10, 30))
    assert result["status"] == "ready"
    assert result["proposed_actions"] == []


def test_unknown_codes_are_rejected_with_valid_values(engine):
    with pytest.raises(ValueError, match="Valid plants"):
        engine.factory_readiness("XX99", "FG-SERUM-50", 10, date(2026, 10, 30))


def test_stock_balance_moves_surplus_to_gap_with_ortools(engine):
    result = engine.stock_balance("FG-PERFUME-100", 14, 0.95)
    assert result["optimization"]["engine"] == "ortools-glop"
    assert result["forecast_engine"] == ["xgboost"]
    dc21 = next(p for p in result["positions"] if p["warehouse"] == "DC21")
    assert dc21["in_transit_within_horizon"] == 600  # SH-880101 arrives 22 Oct after delay
    transfers = result["proposed_actions"]
    assert transfers and all(t["to"] == "DC21" for t in transfers)
    for transfer in transfers:
        source = next(p for p in result["positions"] if p["warehouse"] == transfer["from"])
        assert source["surplus_or_gap"] > 0


def test_supplier_risk_scores(engine):
    packglass = engine.supplier_risk("PackGlass Europe")
    assert packglass["risk_rating"] in ("medium", "high")
    assert any(a["action"] == "issue_supplier_corrective_action_request" for a in packglass["proposed_actions"])
    aroma = engine.supplier_risk("V-100231")
    assert aroma["risk_rating"] == "low"
    bio = engine.supplier_risk("bioactive labs")
    assert bio["single_source"] is True
    assert bio["otif_pct"] == 0.0
    scorecard = engine.supplier_scorecard()["suppliers"]
    assert scorecard[0]["risk_score"] >= scorecard[-1]["risk_score"]


def test_quality_status_links_lots_to_production_orders(engine):
    result = engine.quality_status("FR20", None)
    assert any(i["lot"] == "QL-260011" and i["production_order"] in ("10000102", "10000104") for i in result["production_impacts"])
    assert any(a["action"] == "expedite_quality_release" for a in result["proposed_actions"])


def test_logistics_escalates_long_delays(engine):
    result = engine.logistics_status(None, None)
    escalated = {a["shipment"] for a in result["proposed_actions"]}
    assert escalated == {"SH-880112"}
    assert result["delayed_count"] == 2


def test_inventory_and_kpis(engine):
    overview = engine.inventory_overview("FG-SERUM-50")
    assert len(overview["positions"]) == 3
    kpis = engine.kpis()
    assert kpis["at_risk_count"] >= 2
    assert kpis["quality_lots_open"] == 2
