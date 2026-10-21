"""Deterministic SYNTHETIC SAP fixtures for SupplyChain Insight AI (every record is fictional and labelled synthetic).

One cosmetics factory (FAC-1) and three regional warehouses (WH-A, WH-B, WH-C); 20 finished-product SKUs; 10 critical
materials; approved suppliers; open and historical purchase orders with receipts; inventory batches with quality,
reservation and expiry states; 90 days of demand history; transport lanes; one prior decision for outcome learning.

Planted scenarios (business date 2026-10-21):
  1. Production order PRD-1001: 50,000 x SER-VITC-30 starting 2026-10-27. Pumps PUMP-DISP-24: 30,000 usable at FAC-1,
     4,000 blocked (QA hold), 25,000 confirmed but promised 2026-11-05 (after the need date), 8,000 unconfirmed
     -> exactly 20,000 pumps missing.
  2. SUN-SPF50-100 at WH-B: 1,200 usable vs ~200/day -> ~6 days of cover; WH-C and WH-A hold surplus.
  3. WH-C SUN-SPF50-100 batches: released 3,000 (long dated), released 1,500 near expiry, 800 expired, 700 blocked,
     1,000 reserved for SO-88001, 500 in quality inspection -> only the long-dated released batch is transferable.
  Learning: REC-HIST-0001 predicted Supplier A pump lead time 5 days; SAP goods receipt shows 9 days.
"""
from __future__ import annotations

import hashlib
import json
import random
from datetime import date, timedelta

from backend.scinsight.db import Database, now_iso

TENANT = "scinsight-cosmetics"
OTHER_TENANT = "northwind-pharma"
BUSINESS_DATE = date(2026, 10, 21)
SNAPSHOT_ID = "SAP-SYN-2026-10-21T0600Z"

# Dev/test API keys; deployments override them with SCI_*_KEY environment variables (scripts/gen-env.py).
DEFAULT_KEYS = {
    "agent": "sci-dev-agent-key", "planner": "sci-dev-planner-key", "procurement": "sci-dev-procurement-key",
    "warehouse": "sci-dev-warehouse-key", "logistics": "sci-dev-logistics-key", "quality": "sci-dev-quality-key",
    "director": "sci-dev-director-key", "sap_executor": "sci-dev-sap-executor-key", "mlops": "sci-dev-mlops-key",
    "other_tenant": "sci-dev-other-tenant-key",
}
USERS = [  # key slot, user id, name, roles
    ("agent", "u-flowise-agent", "Flowise agent service", ["agent_service"]),
    ("planner", "u-production-planner", "Camille Laurent (production planner, fictional)", ["planner", "production_planner"]),
    ("procurement", "u-procurement-manager", "Marco Bianchi (procurement manager, fictional)", ["planner", "procurement_manager"]),
    ("warehouse", "u-warehouse-manager", "Lucía Ortega (warehouse manager, fictional)", ["planner", "warehouse_manager"]),
    ("logistics", "u-logistics-manager", "Jonas Weber (logistics manager, fictional)", ["planner", "logistics_manager"]),
    ("quality", "u-quality-manager", "Aiko Tanaka (quality manager, fictional)", ["planner", "quality_manager"]),
    ("director", "u-sc-director", "Elena Rossi (supply-chain director, fictional)", ["planner", "supply_chain_director"]),
    ("sap_executor", "u-sap-executor", "SAP key user (fictional)", ["sap_executor"]),
    ("mlops", "u-mlops", "MLOps engineer (fictional)", ["mlops_engineer"]),
]

LOCATIONS = [
    ("FAC-1", "Lyon factory", "factory", "France", "Lyon", 14),
    ("WH-A", "Warehouse A — Paris", "warehouse", "North", "Paris", 14),
    ("WH-B", "Warehouse B — Madrid", "warehouse", "South-West", "Madrid", 14),
    ("WH-C", "Warehouse C — Milan", "warehouse", "South-East", "Milan", 14),
]
PRODUCTS = [  # sku, name, category, shelf life days, unit cost
    ("SER-VITC-30", "Vitamin C serum 30 ml (pump bottle)", "serum", 540, 6.80), ("SER-HYAL-30", "Hyaluronic serum 30 ml", "serum", 540, 6.20),
    ("SER-RETI-30", "Retinol serum 30 ml", "serum", 450, 7.40), ("SUN-SPF50-100", "Sunscreen SPF50 100 ml", "suncare", 730, 4.10),
    ("SUN-SPF30-200", "Sunscreen SPF30 200 ml", "suncare", 730, 4.90), ("CRM-HYDR-50", "Hydrating cream 50 ml", "skincare", 720, 5.30),
    ("CRM-NIGHT-50", "Night cream 50 ml", "skincare", 720, 5.70), ("CRM-EYE-15", "Eye cream 15 ml", "skincare", 540, 4.40),
    ("CLN-GEL-150", "Cleansing gel 150 ml", "cleansing", 900, 2.60), ("CLN-OIL-200", "Cleansing oil 200 ml", "cleansing", 900, 3.40),
    ("TNR-ROSE-200", "Rose toner 200 ml", "cleansing", 720, 2.90), ("MSK-CLAY-75", "Clay mask 75 ml", "skincare", 720, 3.60),
    ("LIP-BALM-4", "Lip balm 4 g", "lip", 1095, 1.10), ("BDY-LOT-400", "Body lotion 400 ml", "body", 900, 3.80),
    ("SHM-REPR-250", "Repair shampoo 250 ml", "hair", 900, 2.70), ("CND-REPR-250", "Repair conditioner 250 ml", "hair", 900, 2.80),
    ("PRF-EDP-50", "Eau de parfum 50 ml", "fragrance", 1460, 11.50), ("PRF-EDT-100", "Eau de toilette 100 ml", "fragrance", 1460, 9.80),
    ("DEO-ROLL-50", "Roll-on deodorant 50 ml", "body", 900, 1.70), ("HND-CRM-75", "Hand cream 75 ml", "body", 900, 2.20),
]
MATERIALS = [  # material id, name, uom, unit cost, critical
    ("PUMP-DISP-24", "24/410 pump dispenser", "EA", 0.42, 1), ("BTL-GLS-30", "30 ml amber glass bottle", "EA", 0.31, 1),
    ("SER-BASE-VC", "Vitamin C serum base", "KG", 38.0, 1), ("CAP-PUMP-OVR", "Pump overcap", "EA", 0.05, 0),
    ("CRT-SER-30", "Serum folding carton", "EA", 0.09, 0), ("TUB-SUN-100", "100 ml sunscreen tube", "EA", 0.18, 1),
    ("SUN-BASE-50", "SPF50 emulsion base", "KG", 21.0, 1), ("JAR-CRM-50", "50 ml cream jar", "EA", 0.36, 0),
    ("CRM-BASE-HY", "Hydrating cream base", "KG", 24.0, 0), ("LBL-GEN", "Printed label", "EA", 0.02, 0),
]
SUPPLIERS = [  # id, name, country, approved, items [(material, price, moq, contract lead)]
    ("SUP-A", "Alpine Dispensing (synthetic)", "Switzerland", 1, [("PUMP-DISP-24", 0.42, 5000, 5), ("CAP-PUMP-OVR", 0.05, 10000, 5)]),
    ("SUP-B", "Iberia Closures (synthetic)", "Spain", 1, [("PUMP-DISP-24", 0.48, 2000, 7), ("CAP-PUMP-OVR", 0.06, 5000, 7)]),
    ("SUP-C", "Nordic Glassworks (synthetic)", "Denmark", 1, [("BTL-GLS-30", 0.31, 10000, 14)]),
    ("SUP-D", "ChemBase Labs (synthetic)", "France", 1, [("SER-BASE-VC", 38.0, 100, 10), ("SUN-BASE-50", 21.0, 200, 10), ("CRM-BASE-HY", 24.0, 200, 10)]),
    ("SUP-E", "PackPrint Europe (synthetic)", "Germany", 1, [("CRT-SER-30", 0.09, 20000, 8), ("LBL-GEN", 0.02, 50000, 6), ("JAR-CRM-50", 0.36, 5000, 12)]),
    ("SUP-F", "TubeTech (synthetic)", "Italy", 1, [("TUB-SUN-100", 0.18, 10000, 9)]),
    ("SUP-X", "Unvetted Pumps Ltd (synthetic, NOT approved)", "Unknown", 0, [("PUMP-DISP-24", 0.30, 1000, 4)]),
]
LANES = [  # origin, destination, mode, lead days, cost/unit, fixed cost, capacity
    ("WH-C", "WH-B", "road", 2, 0.35, 120.0, 5000), ("WH-A", "WH-B", "road", 3, 0.30, 100.0, 6000),
    ("WH-B", "WH-C", "road", 2, 0.35, 120.0, 5000), ("WH-A", "WH-C", "road", 2, 0.28, 100.0, 6000),
    ("WH-C", "WH-A", "road", 2, 0.28, 100.0, 6000), ("WH-B", "WH-A", "road", 3, 0.30, 100.0, 6000),
    ("FAC-1", "WH-A", "road", 1, 0.15, 60.0, 20000), ("FAC-1", "WH-B", "road", 2, 0.22, 90.0, 20000), ("FAC-1", "WH-C", "road", 1, 0.18, 70.0, 20000),
]
# Demand per day (units) by SKU and warehouse; sunscreen is the planted scenario.
DEMAND = {"SUN-SPF50-100": {"WH-A": 120, "WH-B": 200, "WH-C": 110}, "SER-VITC-30": {"WH-A": 260, "WH-B": 180, "WH-C": 150}}


def key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _d(offset: int) -> str:
    return (BUSINESS_DATE + timedelta(days=offset)).isoformat()


def load(db: Database, keys: dict[str, str] | None = None, reset: bool = False) -> dict:
    """Load the synthetic fixtures (idempotent: rows are replaced by primary key). Returns counts per table."""
    keys = {**DEFAULT_KEYS, **(keys or {})}
    rng = random.Random(20261021)
    t, now = TENANT, now_iso()
    if reset:
        for table in ("rag_chunks", "rag_documents", "retraining_requests", "model_versions", "learning_records", "observed_outcomes",
                      "sap_execution_refs", "human_decisions", "recommendations", "agent_runs", "transport_lanes", "sales_history",
                      "purchase_orders", "supplier_items", "suppliers", "production_orders", "inventory_batches", "bom_components",
                      "materials", "products", "warehouses", "sap_snapshots", "role_assignments", "users", "tenants", "audit_events"):
            db.execute(f"delete from {table}")  # noqa: S608 - fixed table list

    def upsert(table: str, cols: tuple, rows: list[tuple]) -> None:
        placeholders = ",".join("?" * len(cols))
        if db.dialect == "postgres":
            sql = f"insert into {table}({','.join(cols)}) values({placeholders}) on conflict do nothing"  # noqa: S608
        else:
            sql = f"insert or ignore into {table}({','.join(cols)}) values({placeholders})"  # noqa: S608
        db.executemany(sql, rows)

    upsert("tenants", ("id", "name", "industry", "synthetic", "industry_sharing_enabled", "created_at"),
           [(t, "Belleva Cosmetics (synthetic)", "cosmetics", 1, 0, now), (OTHER_TENANT, "Northwind Pharma (synthetic)", "pharmaceutical", 1, 0, now)])
    upsert("users", ("id", "tenant_id", "name", "email", "api_key_hash", "active", "created_at"),
           [(uid, t, name, f"{uid}@belleva.example", key_hash(keys[slot]), 1, now) for slot, uid, name, _ in USERS]
           + [("u-other-tenant", OTHER_TENANT, "Northwind planner (fictional)", "planner@northwind.example", key_hash(keys["other_tenant"]), 1, now)])
    # Key rotation: the configured keys always win over hashes stored by an earlier start (e.g. dev keys).
    db.executemany("update users set api_key_hash=? where id=?",
                   [(key_hash(keys[slot]), uid) for slot, uid, _, _ in USERS] + [(key_hash(keys["other_tenant"]), "u-other-tenant")])
    upsert("role_assignments", ("user_id", "tenant_id", "role"),
           [(uid, t, role) for _, uid, _, roles in USERS for role in roles]
           + [("u-other-tenant", OTHER_TENANT, "planner"), ("u-other-tenant", OTHER_TENANT, "supply_chain_director")])
    upsert("sap_snapshots", ("id", "tenant_id", "source_system", "extracted_at", "as_of_date", "status", "synthetic", "provenance"),
           [(SNAPSHOT_ID, t, "S4HANA-SYNTHETIC", "2026-10-21T06:00:00+00:00", BUSINESS_DATE.isoformat(), "valid", 1,
             "Synthetic fixture generated by backend/scinsight/fixtures.py (seed 20261021); not real SAP data."),
            ("SAP-SYN-NW-2026-10-01", OTHER_TENANT, "S4HANA-SYNTHETIC", "2026-10-01T06:00:00+00:00", "2026-10-01", "valid", 1, "Synthetic second tenant")])
    upsert("warehouses", ("tenant_id", "code", "name", "kind", "region", "city", "target_cover_days"), [(t, *loc) for loc in LOCATIONS]
           + [(OTHER_TENANT, "WH-X", "Northwind DC (synthetic)", "warehouse", "North", "Oslo", 21)])
    upsert("products", ("tenant_id", "sku", "name", "category", "uom", "shelf_life_days", "unit_cost_eur"),
           [(t, sku, name, cat, "EA", life, cost) for sku, name, cat, life, cost in PRODUCTS]
           + [(OTHER_TENANT, "SUN-SPF50-100", "Northwind sunscreen (synthetic)", "suncare", "EA", 730, 4.0)])
    upsert("materials", ("tenant_id", "material_id", "name", "uom", "unit_cost_eur", "critical"), [(t, *m) for m in MATERIALS])

    # ---- BOMs: SER-VITC-30 v2 approved (scenario 1); v3 is a DRAFT (invalid for planning); SER-RETI-30 has a unit mismatch.
    bom = [(t, "SER-VITC-30", "v2", m, q, u, s, "2026-01-01", None, "approved") for m, q, u, s in [
        ("PUMP-DISP-24", 1, "EA", 0), ("BTL-GLS-30", 1, "EA", 0.5), ("SER-BASE-VC", 0.031, "KG", 2.0), ("CAP-PUMP-OVR", 1, "EA", 0), ("CRT-SER-30", 1, "EA", 0)]]
    bom += [(t, "SER-VITC-30", "v3", "PUMP-DISP-24", 1, "EA", 0, "2026-12-01", None, "draft")]
    bom += [(t, "SER-VITC-30", "v1", "PUMP-DISP-24", 1, "EA", 0, "2025-01-01", "2025-12-31", "approved")]  # expired version
    bom += [(t, "SUN-SPF50-100", "v1", m, q, u, s, "2025-06-01", None, "approved") for m, q, u, s in [
        ("TUB-SUN-100", 1, "EA", 0.5), ("SUN-BASE-50", 0.102, "KG", 1.5), ("LBL-GEN", 1, "EA", 1.0)]]
    bom += [(t, "SER-RETI-30", "v1", "SER-BASE-VC", 30, "ML", 2.0, "2026-01-01", None, "approved"),  # ML vs KG stock: unit mismatch
            (t, "SER-RETI-30", "v1", "PUMP-DISP-24", 1, "EA", 0, "2026-01-01", None, "approved")]
    bom += [(t, "CRM-HYDR-50", "v1", m, q, u, s, "2025-06-01", None, "approved") for m, q, u, s in [
        ("JAR-CRM-50", 1, "EA", 0.5), ("CRM-BASE-HY", 0.052, "KG", 1.5), ("LBL-GEN", 1, "EA", 1.0)]]
    upsert("bom_components", ("tenant_id", "sku", "bom_version", "material_id", "qty_per_unit", "uom", "scrap_pct", "valid_from", "valid_to", "status"), bom)

    # ---- inventory batches
    inv = [  # batch, location, item, type, qty, uom, status, expiry, reserved_for
        ("P-REL-01", "FAC-1", "PUMP-DISP-24", "material", 20000, "EA", "released", None, None),
        ("P-REL-02", "FAC-1", "PUMP-DISP-24", "material", 10000, "EA", "released", None, None),
        ("P-BLK-03", "FAC-1", "PUMP-DISP-24", "material", 4000, "EA", "blocked", None, None),
        ("B-GLS-01", "FAC-1", "BTL-GLS-30", "material", 60000, "EA", "released", None, None),
        ("SB-VC-01", "FAC-1", "SER-BASE-VC", "material", 1800, "KG", "released", "2027-03-31", None),
        ("SB-VC-02", "FAC-1", "SER-BASE-VC", "material", 150, "KG", "released", "2026-10-10", None),  # expired base
        ("CAP-01", "FAC-1", "CAP-PUMP-OVR", "material", 55000, "EA", "released", None, None),
        ("CRT-01", "FAC-1", "CRT-SER-30", "material", 52000, "EA", "released", None, None),
        ("TUB-01", "FAC-1", "TUB-SUN-100", "material", 30000, "EA", "released", None, None),
        ("SUNB-01", "FAC-1", "SUN-BASE-50", "material", 2500, "KG", "released", "2027-05-31", None),
        ("LBL-01", "FAC-1", "LBL-GEN", "material", 200000, "EA", "released", None, None),
        ("JAR-01", "FAC-1", "JAR-CRM-50", "material", 18000, "EA", "released", None, None),
        ("CRMB-01", "FAC-1", "CRM-BASE-HY", "material", 900, "KG", "released", "2027-02-28", None),
        # scenario 2 + 3: sunscreen
        ("S-B-01", "WH-B", "SUN-SPF50-100", "product", 1200, "EA", "released", "2027-09-30", None),
        ("S-A-01", "WH-A", "SUN-SPF50-100", "product", 3600, "EA", "released", "2027-08-31", None),
        ("S-C-01", "WH-C", "SUN-SPF50-100", "product", 3000, "EA", "released", "2027-06-30", None),
        ("S-C-02", "WH-C", "SUN-SPF50-100", "product", 1500, "EA", "released", "2026-11-10", None),   # near expiry (20 days)
        ("S-C-03", "WH-C", "SUN-SPF50-100", "product", 800, "EA", "released", "2026-10-15", None),    # expired
        ("S-C-04", "WH-C", "SUN-SPF50-100", "product", 700, "EA", "blocked", "2027-07-31", None),     # QA blocked
        ("S-C-05", "WH-C", "SUN-SPF50-100", "product", 1000, "EA", "reserved", "2027-07-31", "SO-88001"),  # allocated to a customer order
        ("S-C-06", "WH-C", "SUN-SPF50-100", "product", 500, "EA", "quality_inspection", "2027-08-31", None),  # not released
        # serum finished goods
        ("V-A-01", "WH-A", "SER-VITC-30", "product", 5200, "EA", "released", "2027-12-31", None),
        ("V-B-01", "WH-B", "SER-VITC-30", "product", 2100, "EA", "released", "2027-12-31", None),
        ("V-C-01", "WH-C", "SER-VITC-30", "product", 4100, "EA", "released", "2027-11-30", None),
    ]
    for sku, *_ in PRODUCTS:  # every other SKU gets one released batch per warehouse
        if sku in ("SUN-SPF50-100", "SER-VITC-30"):
            continue
        for wh in ("WH-A", "WH-B", "WH-C"):
            inv.append((f"{sku}-{wh}", wh, sku, "product", rng.randint(800, 6000), "EA", "released", _d(rng.randint(120, 700)), None))
    upsert("inventory_batches", ("tenant_id", "batch_id", "location", "item_id", "item_type", "quantity", "uom", "status", "expiry_date", "reserved_for", "snapshot_id"),
           [(t, *row, SNAPSHOT_ID) for row in inv] + [(OTHER_TENANT, "NW-1", "WH-X", "SUN-SPF50-100", "product", 9000, "EA", "released", "2027-12-31", None, "SAP-SYN-NW-2026-10-01")])

    upsert("production_orders", ("tenant_id", "order_id", "sku", "quantity", "uom", "plant", "start_date", "due_date", "status"), [
        (t, "PRD-1001", "SER-VITC-30", 50000, "EA", "FAC-1", "2026-10-27", "2026-10-30", "released"),
        (t, "PRD-1002", "SUN-SPF50-100", 12000, "EA", "FAC-1", "2026-11-09", "2026-11-11", "planned"),
        (t, "PRD-1003", "CRM-HYDR-50", 8000, "EA", "FAC-1", "2026-11-02", "2026-11-04", "planned"),
        (t, "PRD-1004", "SER-RETI-30", 6000, "EA", "FAC-1", "2026-11-16", "2026-11-18", "planned"),
    ])
    sup_rows, item_rows = [], []
    for sid, name, country, approved, items in SUPPLIERS:
        sup_rows.append((t, sid, name, country, approved))
        item_rows += [(t, sid, m, price, moq, lead) for m, price, moq, lead in items]
    upsert("suppliers", ("tenant_id", "supplier_id", "name", "country", "approved"), sup_rows)
    upsert("supplier_items", ("tenant_id", "supplier_id", "material_id", "unit_price_eur", "moq", "contract_lead_time_days"), item_rows)

    # ---- purchase orders: open/confirmed + ~60 historical receipts (lead-time history for estimation and ML)
    pos = [
        (t, "PO-4500021001", "SUP-A", "PUMP-DISP-24", 25000, "EA", "FAC-1", "2026-10-15", "2026-11-05", "confirmed", None, None),  # too late for PRD-1001
        (t, "PO-4500021002", "SUP-A", "PUMP-DISP-24", 8000, "EA", "FAC-1", "2026-10-19", "2026-10-24", "open", None, None),       # not confirmed
        (t, "PO-4500021003", "SUP-C", "BTL-GLS-30", 30000, "EA", "FAC-1", "2026-10-10", "2026-10-29", "confirmed", None, None),
        (t, "PO-4500021004", "SUP-F", "TUB-SUN-100", 20000, "EA", "FAC-1", "2026-10-12", "2026-10-28", "confirmed", None, None),
        # the decision used by the outcome-learning scenario: ordered 2026-09-30, promised 5 days, received 9 days later
        (t, "PO-4500020950", "SUP-A", "PUMP-DISP-24", 25000, "EA", "FAC-1", "2026-09-30", "2026-10-05", "received", "2026-10-09", 25000),
    ]
    actual_mean = {"SUP-A": 8.6, "SUP-B": 7.4, "SUP-C": 14.5, "SUP-D": 10.8, "SUP-E": 8.3, "SUP-F": 9.6}
    n = 0
    for sid, _, _, approved, items in SUPPLIERS:
        if not approved:
            continue
        for material, _, moq, lead in items:
            for k in range(4 if sid in ("SUP-A", "SUP-B") else 2):
                n += 1
                order = BUSINESS_DATE - timedelta(days=200 - n * 3)
                qty = moq * rng.choice([2, 3, 4, 5, 6])
                actual = max(1, round(actual_mean[sid] + rng.uniform(-1.6, 1.6) + (0.00004 * qty if sid == "SUP-A" else 0)))
                promised = order + timedelta(days=lead)
                received = order + timedelta(days=actual)
                if received >= BUSINESS_DATE:
                    continue
                short = 0.97 if (sid == "SUP-E" and k == 1) else 1.0  # one partial delivery (incomplete outcome)
                pos.append((t, f"PO-45000{19000 + n}", sid, material, qty, "EA" if material not in ("SER-BASE-VC", "SUN-BASE-50", "CRM-BASE-HY") else "KG",
                            "FAC-1", order.isoformat(), promised.isoformat(), "received", received.isoformat(), round(qty * short)))
    upsert("purchase_orders", ("tenant_id", "po_id", "supplier_id", "material_id", "quantity", "uom", "plant", "order_date", "promised_date",
                               "status", "received_date", "received_quantity"), pos)

    # ---- 90 days of daily sales history per SKU and warehouse (sunscreen + serum follow DEMAND; others random but stable)
    sales = []
    for sku, *_ in PRODUCTS:
        for wh in ("WH-A", "WH-B", "WH-C"):
            base = DEMAND.get(sku, {}).get(wh) or rng.randint(20, 160)
            for day in range(1, 91):
                weekday = (BUSINESS_DATE - timedelta(days=day)).weekday()
                season = 1.08 if weekday in (4, 5) else 0.97
                sales.append((t, sku, wh, _d(-day), round(base * season * rng.uniform(0.9, 1.1))))
    upsert("sales_history", ("tenant_id", "sku", "warehouse", "day", "quantity"), sales)
    upsert("transport_lanes", ("tenant_id", "lane_id", "origin", "destination", "mode", "lead_days", "cost_per_unit_eur", "fixed_cost_eur", "capacity_units"),
           [(t, f"LN-{o}-{d}", o, d, mode, lead, cost, fixed, cap) for o, d, mode, lead, cost, fixed, cap in LANES])

    # ---- one prior decision with a verified execution, for the Decision Outcome Learning scenario
    calc = {"kind": "lead_time_estimate", "supplier_id": "SUP-A", "material_id": "PUMP-DISP-24", "predicted_lead_time_days": 5,
            "basis": "contract lead time (baseline v0)", "po_id": "PO-4500020950"}
    upsert("agent_runs", ("id", "tenant_id", "user_id", "kind", "request", "result", "snapshot_id", "created_at"),
           [("CALC-HIST-0001", t, "u-flowise-agent", "lead_time_estimate", json.dumps({"supplier_id": "SUP-A"}), json.dumps(calc), "SAP-SYN-2026-09-30", "2026-09-30T08:00:00+00:00")])
    upsert("recommendations", ("id", "tenant_id", "calculation_id", "domain", "title", "proposed_actions", "evidence", "prediction", "risk_level",
                               "status", "idempotency_key", "model_version", "created_by", "created_at", "updated_at"),
           [("REC-HIST-0001", t, "CALC-HIST-0001", "procurement", "Order 25,000 pumps from Supplier A (predicted 5-day lead time)",
             json.dumps([{"action": "purchase_request", "supplier_id": "SUP-A", "material_id": "PUMP-DISP-24", "quantity": 25000}]),
             json.dumps({"source": "synthetic SAP purchasing history", "snapshot": "SAP-SYN-2026-09-30"}),
             json.dumps({"metric": "lead_time_days", "predicted": 5, "po_id": "PO-4500020950"}), "medium", "executed", "hist-0001", "lead-time-baseline-v0",
             "u-flowise-agent", "2026-09-30T08:00:00+00:00", "2026-09-30T09:30:00+00:00")])
    upsert("human_decisions", ("id", "tenant_id", "recommendation_id", "reviewer_id", "reviewer_roles", "decision", "explanation", "modifications", "created_at"),
           [("HD-HIST-0001", t, "REC-HIST-0001", "u-procurement-manager", json.dumps(["procurement_manager"]), "approve",
             "Supplier A is the qualified primary source; approved.", None, "2026-09-30T09:00:00+00:00")])
    upsert("sap_execution_refs", ("id", "tenant_id", "recommendation_id", "sap_document", "doc_type", "executed_at", "recorded_by", "source"),
           [("SX-HIST-0001", t, "REC-HIST-0001", "PO-4500020950", "purchase_order", "2026-09-30T09:30:00+00:00", "u-sap-executor", "manual_sap_execution_record")])
    return {table: db.one(f"select count(*) as n from {table} where tenant_id=?", (t,))["n"]  # noqa: S608
            for table in ("products", "materials", "inventory_batches", "purchase_orders", "sales_history", "transport_lanes", "suppliers")}
