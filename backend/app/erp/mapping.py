"""SAP entity -> SPARC snapshot mapping.

A mapping says, per SPARC section, which OData entity set to read and how each SPARC field is built from it:
  "Material"                         SAP property (a/b follows an expanded navigation property)
  "const:factory"                    fixed value
  "map:InventoryStockType|01=unrestricted,02=inspection,*=blocked"   value table (* = anything else)
Numbers and dates are converted by SPARC field type (OData V2 "/Date(ms)/" and decimal strings included). Nothing is specific
to one customer: custom SAP services or Z-fields are configured, not coded.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# SPARC sections the engine reads, what they are used for, and their fields (required first). Defaults fill optional fields.
SECTIONS: dict[str, dict[str, Any]] = {
    "materials": {"label": "Material master", "usage": "Product and material information", "required": ["code", "description", "type", "uom"],
                  "optional": {"unit_cost": 0.0, "safety_stock": 0.0}},
    "plants": {"label": "Warehouse / plant", "usage": "Warehouse allocation and transfers", "required": ["code", "name", "type"], "optional": {"country": ""}},
    "stock": {"label": "Inventory / stock", "usage": "Warehouse inventory and availability", "required": ["plant", "material", "quantity", "status"],
              "optional": {"batch": "", "expiry": None}},
    "bom": {"label": "Bill of materials", "usage": "Factory material readiness", "required": ["plant", "parent", "component", "quantity"], "optional": {"scrap_pct": 0.0}},
    "production_orders": {"label": "Production orders", "usage": "Factory planning", "required": ["order", "plant", "material", "quantity", "finish_date", "status"], "optional": {}},
    "purchase_orders": {"label": "Purchase orders", "usage": "Procurement planning", "required": ["po", "supplier", "material", "plant", "quantity", "delivery_date", "status"], "optional": {}},
    "suppliers": {"label": "Suppliers", "usage": "Supplier reliability and lead times", "required": ["code", "name"],
                  "optional": {"country": "", "materials": [], "contract_lead_time_days": 0, "approved": True}},
    "sales_orders": {"label": "Sales orders", "usage": "Demand and fulfillment", "required": ["order", "customer", "warehouse", "material", "quantity", "requested_date"],
                     "optional": {"priority": "standard"}},
    "po_history": {"label": "Goods receipts", "usage": "Actual supplier delivery performance",
                   "required": ["po", "supplier", "material", "promised_date", "received_date", "quantity_ordered", "quantity_received"], "optional": {"quality_rejected": 0.0}},
    "quality_lots": {"label": "Quality inspection", "usage": "Blocked or restricted stock", "required": ["lot", "plant", "material", "quantity", "status"],
                     "optional": {"batch": "", "supplier": "", "usage_decision": None, "expected_release": None, "defect": None}},
    "shipments": {"label": "Deliveries / shipments", "usage": "Logistics and fulfillment", "required": ["shipment", "from", "to", "material", "quantity", "eta", "status"],
                  "optional": {"type": "delivery", "mode": "", "carrier": "", "departed": None, "delay_days": 0}},
}
# Not read from SAP: verified decision results come from SPARC's outcome ledger, reconciled against SAP documents.
DERIVED = [{"label": "Business outcomes", "usage": "Verified decision results", "source": "SPARC outcome ledger (reconciled against SAP goods receipts)"}]

NUMERIC = {"quantity", "unit_cost", "safety_stock", "scrap_pct", "quantity_ordered", "quantity_received", "quality_rejected", "contract_lead_time_days", "delay_days"}
DATES = {"expiry", "finish_date", "delivery_date", "requested_date", "promised_date", "received_date", "expected_release", "eta", "departed"}
# rows of these sections must reference known plants/materials (rows outside SPARC's master data are dropped and reported)
REFERENCES = {"stock": ("plant", "material"), "bom": ("plant", "parent", "component"), "purchase_orders": ("plant", "material"),
              "production_orders": ("plant", "material")}
# what the engine needs to keep working: the snapshot sections SapRepository validates
REQUIRED_SECTIONS = ["plants", "materials", "bom", "stock", "purchase_orders", "production_orders"]


class SectionMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    service: str = Field(default="", pattern=r"^(/[A-Za-z0-9_/;=.\-]{1,200})?$")
    entity_set: str = Field(default="", pattern=r"^[A-Za-z0-9_]{0,80}$")
    expand: str = Field(default="", pattern=r"^[A-Za-z0-9_,/]{0,200}$")
    filter: str = Field(default="", max_length=300, pattern=r"^[A-Za-z0-9_ '.,:()\-/=<>]*$")
    fields: dict[str, str] = Field(default_factory=dict)


S4 = "/sap/opu/odata/sap"
# Standard S/4HANA read APIs. Transactional data is read by default; master data (materials, plants, suppliers) is carried over
# from the current snapshot until an administrator enables and maps it (SAP master data rarely matches SPARC 1:1).
DEFAULT_MAPPING: dict[str, dict[str, Any]] = {
    "materials": {"enabled": False, "service": f"{S4}/API_PRODUCT_SRV", "entity_set": "A_Product", "expand": "to_Description",
                  "fields": {"code": "Product", "description": "to_Description/ProductDescription", "type": "map:ProductType|FERT=FG,ROH=RM,VERP=PK,HALB=SFG,*=RM",
                             "uom": "BaseUnit"}},
    "plants": {"enabled": False, "service": f"{S4}/API_PLANT_SRV", "entity_set": "A_Plant", "fields": {"code": "Plant", "name": "PlantName", "type": "const:factory"}},
    "stock": {"enabled": True, "service": f"{S4}/API_MATERIAL_STOCK_SRV", "entity_set": "A_MatlStkInAcctMod",
              "fields": {"plant": "Plant", "material": "Material", "batch": "Batch", "quantity": "MatlWrhsStkQtyInMatlBaseUnit",
                         "status": "map:InventoryStockType|01=unrestricted,02=inspection,*=blocked"}},
    "bom": {"enabled": True, "service": f"{S4}/API_BILL_OF_MATERIAL_SRV", "entity_set": "MaterialBOMItem",
            "fields": {"plant": "Plant", "parent": "Material", "component": "BillOfMaterialComponent", "quantity": "BillOfMaterialItemQuantity",
                       "scrap_pct": "ComponentScrapInPercent"}},
    "production_orders": {"enabled": True, "service": f"{S4}/API_PRODUCTION_ORDER_2_SRV", "entity_set": "A_ProductionOrder_2",
                          "fields": {"order": "ManufacturingOrder", "plant": "ProductionPlant", "material": "Material", "quantity": "TotalQuantity",
                                     "finish_date": "MfgOrderPlannedEndDate", "status": "map:OrderIsReleased|true=released,*=planned"}},
    "purchase_orders": {"enabled": True, "service": f"{S4}/API_PURCHASEORDER_PROCESS_SRV", "entity_set": "A_PurchaseOrderItem", "expand": "to_PurchaseOrder,to_ScheduleLine",
                        "fields": {"po": "PurchaseOrder", "supplier": "to_PurchaseOrder/Supplier", "material": "Material", "plant": "Plant", "quantity": "OrderQuantity",
                                   "delivery_date": "to_ScheduleLine/ScheduleLineDeliveryDate", "status": "const:confirmed"}},
    "suppliers": {"enabled": False, "service": f"{S4}/API_BUSINESS_PARTNER", "entity_set": "A_Supplier", "fields": {"code": "Supplier", "name": "SupplierName"}},
    "sales_orders": {"enabled": True, "service": f"{S4}/API_SALES_ORDER_SRV", "entity_set": "A_SalesOrderItem", "expand": "to_SalesOrder",
                     "fields": {"order": "SalesOrder", "customer": "to_SalesOrder/SoldToParty", "warehouse": "ProductionPlant", "material": "Material",
                                "quantity": "RequestedQuantity", "requested_date": "to_SalesOrder/RequestedDeliveryDate"}},
    "po_history": {"enabled": False, "service": f"{S4}/API_MATERIAL_DOCUMENT_SRV", "entity_set": "A_MaterialDocumentItem", "filter": "GoodsMovementType eq '101'",
                   "fields": {"po": "PurchaseOrder", "supplier": "Supplier", "material": "Material", "promised_date": "", "received_date": "PostingDate",
                              "quantity_ordered": "", "quantity_received": "QuantityInEntryUnit"}},
    "quality_lots": {"enabled": False, "service": f"{S4}/API_INSPECTIONLOT_SRV", "entity_set": "A_InspectionLot",
                     "fields": {"lot": "InspectionLot", "plant": "Plant", "material": "Material", "batch": "Batch", "quantity": "InspectionLotQuantity", "status": "const:inspection"}},
    "shipments": {"enabled": False, "service": "", "entity_set": "", "fields": {}},
}


def default_mapping() -> dict[str, SectionMapping]:
    return {k: SectionMapping(**v) for k, v in DEFAULT_MAPPING.items()}


_ODATA_DATE = re.compile(r"/Date\((-?\d+)(?:[+-]\d+)?\)/")


def _get(row: Any, path: str) -> Any:
    for part in path.split("/"):
        if isinstance(row, dict) and "results" in row and isinstance(row["results"], list):  # expanded collection (V2)
            row = row["results"][0] if row["results"] else None
        if isinstance(row, list):  # expanded collection (V4)
            row = row[0] if row else None
        if not isinstance(row, dict):
            return None
        row = row.get(part)
    return row


def resolve(row: dict, expr: str) -> Any:
    if expr.startswith("const:"):
        return expr[6:]
    if expr.startswith("map:"):
        path, _, table = expr[4:].partition("|")
        value = _get(row, path)
        pairs = dict(p.split("=", 1) for p in table.split(",") if "=" in p)
        return pairs.get(str(value).lower() if isinstance(value, bool) else str(value), pairs.get("*", value))
    return _get(row, expr)


def convert(field: str, value: Any) -> Any:
    if value in (None, ""):
        return None
    if field in NUMERIC:
        return float(value)
    if field in DATES:
        text = str(value)
        m = _ODATA_DATE.fullmatch(text)
        if m:
            return datetime.fromtimestamp(int(m.group(1)) / 1000, tz=timezone.utc).date().isoformat()
        return text[:10]
    return value if isinstance(value, (list, bool, int, float)) else str(value).strip()


def transform(section: str, rows: list[dict], fields: dict[str, str]) -> tuple[list[dict], list[str]]:
    """Map SAP rows to SPARC rows; rows missing a required field are rejected with a reason (never silently filled)."""
    spec = SECTIONS[section]
    out, errors = [], []
    for i, row in enumerate(rows):
        item: dict[str, Any] = {}
        try:
            for field, expr in fields.items():
                if expr:
                    item[field] = convert(field, resolve(row, expr))
        except (TypeError, ValueError) as exc:
            errors.append(f"{section} row {i + 1}: {exc}")
            continue
        missing = [f for f in spec["required"] if item.get(f) in (None, "")]
        if missing:
            errors.append(f"{section} row {i + 1}: missing {', '.join(missing)}")
            continue
        for field, default in spec["optional"].items():
            item.setdefault(field, default)
            if item[field] is None and default is not None:
                item[field] = default
        out.append(item)
    return out, errors


def validate_mapping(mapping: dict[str, SectionMapping], metadata: dict[str, set[str]] | None = None) -> list[str]:
    """Problems that block activation. metadata = {entity set: properties + navigation properties} from $metadata, when known."""
    problems: list[str] = []
    for section, m in mapping.items():
        if section not in SECTIONS:
            problems.append(f"Unknown SPARC section {section}")
            continue
        if not m.enabled:
            continue
        label = SECTIONS[section]["label"]
        if not m.service or not m.entity_set:
            problems.append(f"{label}: service path and entity set are required")
            continue
        known = set(SECTIONS[section]["required"]) | set(SECTIONS[section]["optional"])
        for field in set(m.fields) - known:
            problems.append(f"{label}: {field} is not a SPARC field")
        for field in SECTIONS[section]["required"]:
            if not m.fields.get(field):
                problems.append(f"{label}: required field {field} is not mapped")
        if metadata is not None:
            props = metadata.get(m.entity_set)
            if props is None:
                problems.append(f"{label}: entity set {m.entity_set} not found in {m.service}/$metadata")
                continue
            for field, expr in m.fields.items():
                if not expr or expr.startswith("const:"):
                    continue
                first = (expr[4:].partition("|")[0] if expr.startswith("map:") else expr).split("/")[0]
                if first not in props:
                    problems.append(f"{label}: {field} -> {first} is not a property of {m.entity_set}")
    return problems
