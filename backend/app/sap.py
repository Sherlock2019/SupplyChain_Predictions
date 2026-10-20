"""Read-only SAP S/4HANA mock: validated snapshot plus OData-shaped entity sets.

Production replaces the JSON snapshot with a read-only extract (CDS views / OData) and keeps this interface.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

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


class SapRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data = json.loads(self.path.read_text(encoding="utf-8"))
        self._validate()

    def _validate(self) -> None:
        required = {"snapshot", "plants", "materials", "bom", "stock", "purchase_orders", "production_orders", "lanes"}
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
        if not self._data["snapshot"].get("read_only"):
            errors.append("SAP adapter must declare read_only=true")
        if errors:
            raise ValueError("; ".join(errors))

    @property
    def as_of(self) -> date:
        """Business date of the extract; all date logic is relative to it so results are reproducible."""
        raw = self._data["snapshot"].get("as_of_date")
        if raw:
            return date.fromisoformat(raw)
        return datetime.fromisoformat(self._data["snapshot"]["extracted_at"]).date()

    @property
    def snapshot(self) -> dict[str, Any]:
        extracted = datetime.fromisoformat(self._data["snapshot"]["extracted_at"])
        age_hours = (datetime.now(timezone.utc) - extracted).total_seconds() / 3600
        return {**self._data["snapshot"], "age_hours": round(max(age_hours, 0), 2), "validated": True}

    def has(self, name: str) -> bool:
        return name in self._data

    def section(self, name: str) -> Any:
        if name not in self._data:
            raise KeyError(name)
        return deepcopy(self._data[name])

    def codes(self, section: str) -> set[str]:
        return {row["code"] for row in self._data[section]}

    def validate_codes(self, *, plant: str | None = None, material: str | None = None) -> None:
        if plant and plant not in self.codes("plants"):
            raise ValueError(f"Unknown plant {plant}. Valid plants: {', '.join(sorted(self.codes('plants')))}")
        if material and material not in self.codes("materials"):
            raise ValueError(f"Unknown material {material}. Valid materials: {', '.join(sorted(self.codes('materials')))}")

    def material(self, code: str) -> dict[str, Any]:
        self.validate_codes(material=code)
        return next(deepcopy(row) for row in self._data["materials"] if row["code"] == code)

    def supplier(self, name_or_code: str) -> dict[str, Any]:
        key = name_or_code.strip().lower()
        for row in self._data.get("suppliers", []):
            if key in (row["code"].lower(), row["name"].lower()):
                return deepcopy(row)
        names = ", ".join(row["name"] for row in self._data.get("suppliers", []))
        raise ValueError(f"Unknown supplier {name_or_code}. Valid suppliers: {names}")

    def stock_rows(self, plant: str, material: str) -> list[dict[str, Any]]:
        return [deepcopy(row) for row in self._data["stock"] if row["plant"] == plant and row["material"] == material]

    def on_hand(self, plant: str, material: str, *, unrestricted_only: bool = True) -> float:
        self.validate_codes(plant=plant, material=material)
        total = 0.0
        for row in self.stock_rows(plant, material):
            if unrestricted_only and row["status"] != "unrestricted":
                continue
            if row.get("expiry") and date.fromisoformat(row["expiry"]) < self.as_of:
                continue
            total += float(row["quantity"])
        return round(total, 3)

    def odata(self, entity: str, *, top: int = 200, plant: str | None = None, material: str | None = None, supplier: str | None = None) -> dict:
        section = ODATA_ENTITIES.get(entity)
        if section is None or section not in self._data:
            raise KeyError(entity)
        rows = self.section(section)
        if isinstance(rows, dict):
            rows = [{"material": key, **value} for key, value in rows.items()]
        if plant:
            rows = [row for row in rows if plant in (row.get("plant"), row.get("code"), row.get("warehouse"), row.get("from"), row.get("to"))]
        if material:
            rows = [row for row in rows if material in (row.get("material"), row.get("code"), row.get("parent"), row.get("component"))]
        if supplier:
            rows = [row for row in rows if supplier.lower() in (str(row.get("supplier", "")).lower(), str(row.get("name", "")).lower())]
        return {
            "@odata.context": f"$metadata#{entity}",
            "@odata.count": len(rows),
            "value": rows[: min(top, 1000)],
            "__snapshot": self._data["snapshot"]["id"],
        }

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
