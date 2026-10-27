# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/sap.py
# What this module is: the read-only SAP S/4HANA adapter of the SPARC gateway. It loads a JSON snapshot (data/sap_mock.json or a
# tenant file), validates referential integrity, and serves OData-shaped entity sets (A_MaterialStock, A_PurchaseOrderItem, ...).
# There is no write method at all; the gateway answers 405 to every SAP write verb.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Read-only SAP S/4HANA mock: validated snapshot plus OData-shaped entity sets.

Production replaces the JSON snapshot with a read-only extract (CDS views / OData) and keeps this interface.
"""
from __future__ import annotations

import json
# deepcopy: callers receive copies, so they can never modify the cached snapshot.
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# OData entity set name (as in SAP APIs) -> section of the JSON snapshot.
ODATA_ENTITIES = {
    "A_Product": "materials",
    "A_Plant": "plants",
    "A_Supplier": "suppliers",
    "A_BillOfMaterialItem": "bom",
    "A_MaterialStock": "stock",
    "A_PurchaseOrderItem": "purchase_orders",
    "A_PurchaseOrderHistory": "po_history",
    "A_ProductionOrder": "production_orders",
    "A_InspectionLot": "quality_lots",
    "A_SalesOrderItem": "sales_orders",
    "A_Shipment": "shipments",
    "A_TransportLane": "lanes",
    "A_PhysInventoryDocItem": "stocktake_counts",
    "A_MaterialDocumentItem": "goods_movements",
}


# ===== CLASS: SapRepository =====
# ID: F0401 · class · used
# ORIGINAL FILE: backend/app/sap.py:31-148
# ROLE: Read-only repository over one SAP snapshot file; every engine calculation reads SAP data through it.
# FIELDS:
#   path: Path, _data: dict (the parsed snapshot).
# CALLED BY:
#   <- F0452 LocalBackend.__init__() (references)
#   <- F0483 build_backend() (calls)
#   <- F0193 SupplyChainEngine.__init__() (references)
#   <- F0393 TenantRegistry.get() (calls)
#   <- F0922 engine() (calls)
#   <- F0933 engine() (calls)
#   <- F0943 engine() (calls)
#   <- F0966 test_network_map_tiers_and_sourcing() (calls)
# CALLS:
#   (none found)
class SapRepository:
    # ===== FUNCTION: SapRepository.__init__() =====
    # ID: F0402 · method · used (framework)
    # ORIGINAL FILE: backend/app/sap.py:32-35
    # ROLE: Load and validate the snapshot file.
    # INPUTS:
    #   path: str | Path -> JSON snapshot.
    # OUTPUT:
    #   None (ValueError when invalid).
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0403 SapRepository._validate() (calls)
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data = json.loads(self.path.read_text(encoding="utf-8"))
        self._validate()

    # ===== FUNCTION: SapRepository._validate() =====
    # ID: F0403 · method · used (framework)
    # ORIGINAL FILE: backend/app/sap.py:37-59
    # ROLE: Data-quality gate at load time: required sections, valid plant/material references, no negative stock, read_only flag.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   None (ValueError listing every error).
    # CALLED BY:
    #   <- F0402 SapRepository.__init__() (calls)
    # CALLS:
    #   (none found)
    def _validate(self) -> None:
        required = {"snapshot", "plants", "materials", "bom", "stock", "purchase_orders", "production_orders", "lanes"}
        # Set difference: required sections absent from the file.
        missing = required - self._data.keys()
        if missing:
            raise ValueError(f"SAP snapshot is missing sections: {sorted(missing)}")
        plants = {row["code"] for row in self._data["plants"]}
        materials = {row["code"] for row in self._data["materials"]}
        errors: list[str] = []
        for row in self._data["stock"]:
            if row["plant"] not in plants or row["material"] not in materials:
                errors.append(f"Invalid stock reference {row}")
            if float(row["quantity"]) < 0:
                errors.append(f"Negative stock {row}")
        for row in self._data["bom"]:
            if row["plant"] not in plants or row["parent"] not in materials or row["component"] not in materials:
                errors.append(f"Invalid BOM reference {row}")
        for row in self._data["purchase_orders"]:
            if row["plant"] not in plants or row["material"] not in materials:
                errors.append(f"Invalid PO reference {row}")
        # The snapshot must declare itself read-only.
        if not self._data["snapshot"].get("read_only"):
            errors.append("SAP adapter must declare read_only=true")
        if errors:
            raise ValueError("; ".join(errors))

    # ===== FUNCTION: SapRepository.as_of() =====
    # ID: F0404 · method · used
    # ORIGINAL FILE: backend/app/sap.py:61-67
    # ROLE: Business date of the extract (all date logic is relative to it, so results are reproducible).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   date -> snapshot.as_of_date, else the date part of extracted_at.
    # CALLED BY:
    #   <- F0197 SupplyChainEngine.factory_readiness() (references)
    #   <- F0198 SupplyChainEngine.stock_balance() (references)
    #   <- F0201 SupplyChainEngine.supplier_risk() (references)
    #   <- F0202 SupplyChainEngine.supplier_scorecard() (references)
    #   <- F0203 SupplyChainEngine.quality_status() (references)
    #   <- F0204 SupplyChainEngine.logistics_status() (references)
    #   <- F0205 SupplyChainEngine.inventory_overview() (references)
    #   <- F0206 SupplyChainEngine.sales_order_fulfilment() (references)
    #   <- F0207 SupplyChainEngine.stocktake_reconciliation() (references)
    #   <- F0208 SupplyChainEngine.production_overview() (references)
    #   <- F0209 SupplyChainEngine.forecast_vs_actuals() (references)
    #   <- F0210 SupplyChainEngine.position_health() (references)
    # CALLS:
    #   (none found)
    @property
    def as_of(self) -> date:
        """Business date of the extract; all date logic is relative to it so results are reproducible."""
        raw = self._data["snapshot"].get("as_of_date")
        if raw:
            return date.fromisoformat(raw)
        return datetime.fromisoformat(self._data["snapshot"]["extracted_at"]).date()

    # ===== FUNCTION: SapRepository.snapshot() =====
    # ID: F0405 · method · used
    # ORIGINAL FILE: backend/app/sap.py:69-73
    # ROLE: Snapshot metadata + its age in hours and a "validated" flag (shown on every API response).
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0453 LocalBackend._save() (references)
    #   <- F0454 LocalBackend.snapshot() (references)
    #   <- F0461 LocalBackend.inventory() (references)
    #   <- F0248 InsightEngine.insights() (references)
    #   <- F0023 create_app.save() (references)
    #   <- F0025 create_app.health() (references)
    #   <- F0026 create_app.ready() (references)
    #   <- F0031 create_app.status() (references)
    #   <- F0033 create_app.snapshot() (references)
    #   <- F0059 create_app.record_outcome() (references)
    #   <- F0066 create_app.get_insights() (references)
    #   <- F0073 create_app.inventory() (references)
    # CALLS:
    #   (none found)
    @property
    def snapshot(self) -> dict[str, Any]:
        extracted = datetime.fromisoformat(self._data["snapshot"]["extracted_at"])
        age_hours = (datetime.now(timezone.utc) - extracted).total_seconds() / 3600
        return {**self._data["snapshot"], "age_hours": round(max(age_hours, 0), 2), "validated": True}

    # ===== FUNCTION: SapRepository.has() =====
    # ID: F0406 · method · used
    # ORIGINAL FILE: backend/app/sap.py:75-76
    # ROLE: Does the snapshot contain a section?
    # INPUTS:
    #   name: str.
    # OUTPUT:
    #   bool.
    # CALLED BY:
    #   <- F0196 SupplyChainEngine._in_transit_to() (calls)
    #   <- F0197 SupplyChainEngine.factory_readiness() (calls)
    #   <- F0212 SupplyChainEngine.product_360() (calls)
    #   <- F0224 SupplyChainEngine.network_map() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    # CALLS:
    #   (none found)
    def has(self, name: str) -> bool:
        return name in self._data

    # ===== FUNCTION: SapRepository.section() =====
    # ID: F0407 · method · used
    # ORIGINAL FILE: backend/app/sap.py:78-81
    # ROLE: A deep copy of one snapshot section.
    # INPUTS:
    #   name: str.
    # OUTPUT:
    #   Any (KeyError when missing).
    # CALLED BY:
    #   <- F0454 LocalBackend.snapshot() (calls)
    #   <- F0231 Dashboards.product_scope() (calls)
    #   <- F0237 Dashboards._inventory() (calls)
    #   <- F0238 Dashboards._sales() (calls)
    #   <- F0240 Dashboards._procurement() (calls)
    #   <- F0194 SupplyChainEngine._confirmed_pos() (calls)
    #   <- F0195 SupplyChainEngine._warehouses() (calls)
    #   <- F0196 SupplyChainEngine._in_transit_to() (calls)
    #   <- F0197 SupplyChainEngine.factory_readiness() (calls)
    #   <- F0198 SupplyChainEngine.stock_balance() (calls)
    #   <- F0199 SupplyChainEngine.demand_forecast() (calls)
    #   <- F0200 SupplyChainEngine.what_if() (calls)
    # CALLS:
    #   (none found)
    def section(self, name: str) -> Any:
        if name not in self._data:
            raise KeyError(name)
        return deepcopy(self._data[name])

    # ===== FUNCTION: SapRepository.codes() =====
    # ID: F0408 · method · used
    # ORIGINAL FILE: backend/app/sap.py:83-84
    # ROLE: Set of the "code" values of a section (plants, materials).
    # INPUTS:
    #   section: str.
    # OUTPUT:
    #   set[str].
    # CALLED BY:
    #   <- F0409 SapRepository.validate_codes() (calls)
    # CALLS:
    #   (none found)
    def codes(self, section: str) -> set[str]:
        return {row["code"] for row in self._data[section]}

    # ===== FUNCTION: SapRepository.validate_codes() =====
    # ID: F0409 · method · used
    # ORIGINAL FILE: backend/app/sap.py:86-90
    # ROLE: Validate a plant and/or material code; the error lists the valid codes so an agent can correct itself.
    # INPUTS:
    #   plant: str | None, material: str | None (keyword-only because of the `*`).
    # OUTPUT:
    #   None (ValueError -> 422 through the gateway's exception handler).
    # CALLED BY:
    #   <- F0197 SupplyChainEngine.factory_readiness() (calls)
    #   <- F0198 SupplyChainEngine.stock_balance() (calls)
    #   <- F0199 SupplyChainEngine.demand_forecast() (calls)
    #   <- F0203 SupplyChainEngine.quality_status() (calls)
    #   <- F0204 SupplyChainEngine.logistics_status() (calls)
    #   <- F0205 SupplyChainEngine.inventory_overview() (calls)
    #   <- F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    #   <- F0209 SupplyChainEngine.forecast_vs_actuals() (calls)
    #   <- F0212 SupplyChainEngine.product_360() (calls)
    #   <- F0219 SupplyChainEngine.supplier_lead_time() (calls)
    #   <- F0220 SupplyChainEngine.sales_outlook() (calls)
    #   <- F0222 SupplyChainEngine.site_360() (calls)
    # CALLS:
    #   -> F0408 SapRepository.codes() (calls)
    def validate_codes(self, *, plant: str | None = None, material: str | None = None) -> None:
        if plant and plant not in self.codes("plants"):
            raise ValueError(f"Unknown plant {plant}. Valid plants: {', '.join(sorted(self.codes('plants')))}")
        if material and material not in self.codes("materials"):
            raise ValueError(f"Unknown material {material}. Valid materials: {', '.join(sorted(self.codes('materials')))}")

    # ===== FUNCTION: SapRepository.material() =====
    # ID: F0410 · method · used
    # ORIGINAL FILE: backend/app/sap.py:92-94
    # ROLE: Material master record.
    # INPUTS:
    #   code: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0231 Dashboards.product_scope() (calls)
    #   <- F0232 Dashboards.build() (calls)
    #   <- F0235 Dashboards._mentions() (calls)
    #   <- F0237 Dashboards._inventory() (calls)
    #   <- F0197 SupplyChainEngine.factory_readiness() (calls)
    #   <- F0198 SupplyChainEngine.stock_balance() (calls)
    #   <- F0201 SupplyChainEngine.supplier_risk() (calls)
    #   <- F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    #   <- F0207 SupplyChainEngine.stocktake_reconciliation() (calls)
    #   <- F0212 SupplyChainEngine.product_360() (calls)
    #   <- F0213 SupplyChainEngine.product_brief() (calls)
    #   <- F0225 SupplyChainEngine.expiry_risk() (calls)
    # CALLS:
    #   -> F0409 SapRepository.validate_codes() (calls)
    def material(self, code: str) -> dict[str, Any]:
        self.validate_codes(material=code)
        return next(deepcopy(row) for row in self._data["materials"] if row["code"] == code)

    # ===== FUNCTION: SapRepository.supplier() =====
    # ID: F0411 · method · used
    # ORIGINAL FILE: backend/app/sap.py:96-102
    # ROLE: Supplier record by code or name (case-insensitive).
    # INPUTS:
    #   name_or_code: str.
    # OUTPUT:
    #   dict (ValueError listing valid suppliers when unknown).
    # CALLED BY:
    #   <- F0234 Dashboards._supplier_rows() (calls)
    #   <- F0201 SupplyChainEngine.supplier_risk() (calls)
    #   <- F0219 SupplyChainEngine.supplier_lead_time() (calls)
    #   <- F0261 RoleCenter._facts() (calls)
    #   <- F0270 RoleCenter.industry_kpis() (calls)
    # CALLS:
    #   (none found)
    def supplier(self, name_or_code: str) -> dict[str, Any]:
        key = name_or_code.strip().lower()
        for row in self._data.get("suppliers", []):
            if key in (row["code"].lower(), row["name"].lower()):
                return deepcopy(row)
        names = ", ".join(row["name"] for row in self._data.get("suppliers", []))
        raise ValueError(f"Unknown supplier {name_or_code}. Valid suppliers: {names}")

    # ===== FUNCTION: SapRepository.stock_rows() =====
    # ID: F0412 · method · used
    # ORIGINAL FILE: backend/app/sap.py:104-105
    # ROLE: Stock rows of one material at one plant.
    # INPUTS:
    #   plant: str, material: str.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0197 SupplyChainEngine.factory_readiness() (calls)
    #   <- F0413 SapRepository.on_hand() (calls)
    # CALLS:
    #   (none found)
    def stock_rows(self, plant: str, material: str) -> list[dict[str, Any]]:
        return [deepcopy(row) for row in self._data["stock"] if row["plant"] == plant and row["material"] == material]

    # ===== FUNCTION: SapRepository.on_hand() =====
    # ID: F0413 · method · used
    # ORIGINAL FILE: backend/app/sap.py:107-116
    # ROLE: On-hand quantity: unrestricted (usable) stock only by default, never expired stock.
    # INPUTS:
    #   plant: str, material: str, unrestricted_only: bool (keyword-only, default True).
    # OUTPUT:
    #   float -> rounded to 3 decimals.
    # CALLED BY:
    #   <- F0197 SupplyChainEngine.factory_readiness() (calls)
    #   <- F0198 SupplyChainEngine.stock_balance() (calls)
    #   <- F0205 SupplyChainEngine.inventory_overview() (calls)
    #   <- F0206 SupplyChainEngine.sales_order_fulfilment() (calls)
    #   <- F0210 SupplyChainEngine.position_health() (calls)
    #   <- F0212 SupplyChainEngine.product_360() (calls)
    #   <- F0226 SupplyChainEngine.kpis() (calls)
    # CALLS:
    #   -> F0409 SapRepository.validate_codes() (calls)
    #   -> F0412 SapRepository.stock_rows() (calls)
    #   -> F0404 SapRepository.as_of() (references)
    def on_hand(self, plant: str, material: str, *, unrestricted_only: bool = True) -> float:
        self.validate_codes(plant=plant, material=material)
        total = 0.0
        for row in self.stock_rows(plant, material):
            # SAP stock types: only "unrestricted" counts (quality-inspection and blocked stock do not).
            if unrestricted_only and row["status"] != "unrestricted":
                continue
            if row.get("expiry") and date.fromisoformat(row["expiry"]) < self.as_of:
                continue
            total += float(row["quantity"])
        return round(total, 3)

    # ===== FUNCTION: SapRepository.odata() =====
    # ID: F0414 · method · used
    # ORIGINAL FILE: backend/app/sap.py:118-136
    # ROLE: OData-shaped read of an entity set with optional filters ($top, plant, material, supplier).
    # INPUTS:
    #   entity: str (e.g. "A_MaterialStock"), top: int, plant / material / supplier: str | None (keyword-only).
    # OUTPUT:
    #   dict -> {"@odata.context", "@odata.count", "value": rows[:top], "__snapshot"} (KeyError for an unknown entity -> 404).
    # CALLED BY:
    #   <- F0038 create_app.sap_odata() (calls)
    #   <- F0102 create_app.poc_sap_inventory() (calls)
    #   <- F0103 create_app.poc_sap_production_orders() (calls)
    # CALLS:
    #   -> F0407 SapRepository.section() (calls)
    def odata(self, entity: str, *, top: int = 200, plant: str | None = None, material: str | None = None, supplier: str | None = None) -> dict:
        section = ODATA_ENTITIES.get(entity)
        if section is None or section not in self._data:
            raise KeyError(entity)
        rows = self.section(section)
        # Sections stored as {material: {...}} are turned into rows.
        if isinstance(rows, dict):
            rows = [{"material": key, **value} for key, value in rows.items()]
        # The plant filter matches any of the location-like fields of the different entities.
        if plant:
            rows = [row for row in rows if plant in (row.get("plant"), row.get("code"), row.get("warehouse"), row.get("from"), row.get("to"))]
        if material:
            rows = [row for row in rows if material in (row.get("material"), row.get("code"), row.get("parent"), row.get("component"))]
        if supplier:
            rows = [row for row in rows if supplier.lower() in (str(row.get("supplier", "")).lower(), str(row.get("name", "")).lower())]
        return {
            "@odata.context": f"$metadata#{entity}",
            "@odata.count": len(rows),
            # Hard cap of 1000 rows whatever $top says.
            "value": rows[: min(top, 1000)],
            "__snapshot": self._data["snapshot"]["id"],
        }

    # ===== FUNCTION: SapRepository.metadata() =====
    # ID: F0415 · method · used
    # ORIGINAL FILE: backend/app/sap.py:138-148
    # ROLE: $metadata of the read-only OData service: entity sets and row counts.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0036 create_app.sap_metadata() (calls)
    # CALLS:
    #   (none found)
    def metadata(self) -> dict:
        return {
            "service": "ZSCM_COPILOT_SRV",
            "read_only": True,
            "snapshot": self._data["snapshot"]["id"],
            "entity_sets": [
                {"name": entity, "section": section, "rows": len(self._data.get(section, []))}
                for entity, section in ODATA_ENTITIES.items()
                if section in self._data
            ],
        }
