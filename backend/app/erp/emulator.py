"""SAP S/4HANA OData V2 emulator — DEVELOPMENT AND TEST ONLY (never mounted when APP_ENV is staging or production).

Serves the standard read APIs SPARC's default mapping uses (API_PRODUCT_SRV, API_MATERIAL_STOCK_SRV, ...) with SAP property
names, OData V2 envelopes ({"d": {"results": [...]}}, "/Date(ms)/", decimal strings, $metadata XML, $top/$skip/$expand,
sap-client, Basic auth). Its data is a customer snapshot re-expressed the way SAP returns it, moved to today's date and with
unrestricted stock +10%, so a sync from it produces a visibly different snapshot. It is a mock, not a real SAP system.
"""
from __future__ import annotations

import base64
import json
import secrets
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response

USER = "SPARC_COMM"
CLIENT = "100"


def _odate(iso: str | None) -> str | None:
    if not iso:
        return None
    ms = int(datetime.fromisoformat(iso[:10]).replace(tzinfo=timezone.utc).timestamp() * 1000)
    return f"/Date({ms})/"


def _num(v: Any) -> str:
    return f"{float(v):.3f}"


def build_entities(snapshot: dict, today: date | None = None) -> dict[str, dict[str, list[dict]]]:
    """{service: {entity set: rows}} in SAP shape, from a SPARC snapshot."""
    shift = (today or date.today()) - date.fromisoformat(snapshot["snapshot"]["as_of_date"])

    def d(iso: str | None) -> str | None:
        return _odate((date.fromisoformat(iso[:10]) + shift).isoformat()) if iso else None

    sup_code = {s["name"]: s["code"] for s in snapshot.get("suppliers", [])}
    ptype = {"FG": "FERT", "RM": "ROH", "PK": "VERP", "SFG": "HALB"}
    stype = {"unrestricted": "01", "inspection": "02", "blocked": "07"}
    return {
        "API_PRODUCT_SRV": {"A_Product": [{"Product": m["code"], "ProductType": ptype.get(m["type"], "ROH"), "BaseUnit": m["uom"],
                                           "to_Description": {"results": [{"Product": m["code"], "Language": "EN", "ProductDescription": m["description"]}]}}
                                          for m in snapshot["materials"]]},
        "API_PLANT_SRV": {"A_Plant": [{"Plant": p["code"], "PlantName": p["name"]} for p in snapshot["plants"]]},
        "API_MATERIAL_STOCK_SRV": {"A_MatlStkInAcctMod": [
            {"Material": s["material"], "Plant": s["plant"], "StorageLocation": "0001", "Batch": s.get("batch", ""), "InventoryStockType": stype.get(s["status"], "07"),
             "MatlWrhsStkQtyInMatlBaseUnit": _num(round(s["quantity"] * 1.1) if s["status"] == "unrestricted" else s["quantity"]), "MaterialBaseUnit": "EA"}
            for s in snapshot["stock"]]},
        "API_BILL_OF_MATERIAL_SRV": {"MaterialBOMItem": [
            {"Material": b["parent"], "Plant": b["plant"], "BillOfMaterialComponent": b["component"], "BillOfMaterialItemQuantity": _num(b["quantity"]),
             "ComponentScrapInPercent": _num(b.get("scrap_pct", 0))} for b in snapshot["bom"]]},
        "API_PRODUCTION_ORDER_2_SRV": {"A_ProductionOrder_2": [
            {"ManufacturingOrder": o["order"], "ProductionPlant": o["plant"], "Material": o["material"], "TotalQuantity": _num(o["quantity"]),
             "MfgOrderPlannedEndDate": d(o["finish_date"]), "OrderIsReleased": o["status"] == "released"} for o in snapshot["production_orders"]]},
        "API_PURCHASEORDER_PROCESS_SRV": {"A_PurchaseOrderItem": [
            {"PurchaseOrder": p["po"], "PurchaseOrderItem": "10", "Material": p["material"], "Plant": p["plant"], "OrderQuantity": _num(p["quantity"]),
             "to_PurchaseOrder": {"PurchaseOrder": p["po"], "Supplier": sup_code.get(p["supplier"], p["supplier"])},
             "to_ScheduleLine": {"results": [{"ScheduleLine": "1", "ScheduleLineDeliveryDate": d(p["delivery_date"])}]}} for p in snapshot["purchase_orders"]]},
        "API_BUSINESS_PARTNER": {"A_Supplier": [{"Supplier": s["code"], "SupplierName": s["name"]} for s in snapshot.get("suppliers", [])]},
        "API_SALES_ORDER_SRV": {"A_SalesOrderItem": [
            {"SalesOrder": o["order"], "SalesOrderItem": "10", "Material": o["material"], "RequestedQuantity": _num(o["quantity"]), "ProductionPlant": o["warehouse"],
             "to_SalesOrder": {"SalesOrder": o["order"], "SoldToParty": o["customer"], "RequestedDeliveryDate": d(o["requested_date"])}}
            for o in snapshot.get("sales_orders", [])]},
        "API_INSPECTIONLOT_SRV": {"A_InspectionLot": [
            {"InspectionLot": q["lot"], "Plant": q["plant"], "Material": q["material"], "Batch": q.get("batch", ""), "InspectionLotQuantity": _num(q["quantity"])}
            for q in snapshot.get("quality_lots", [])]},
        "API_MATERIAL_DOCUMENT_SRV": {"A_MaterialDocumentItem": [
            {"MaterialDocument": f"50000{i:05d}", "GoodsMovementType": "101", "PurchaseOrder": h["po"], "Supplier": sup_code.get(h["supplier"], h["supplier"]),
             "Material": h["material"], "PostingDate": d(h.get("received_date")), "QuantityInEntryUnit": _num(h.get("quantity_received", 0))}
            for i, h in enumerate(snapshot.get("po_history", []))]},
    }


def metadata_xml(service: str, sets: dict[str, list[dict]]) -> str:
    types = []
    for name, rows in sets.items():
        sample = rows[0] if rows else {}
        props = "".join(f'<Property Name="{k}" Type="Edm.String"/>' for k, v in sample.items() if not isinstance(v, dict))
        navs = "".join(f'<NavigationProperty Name="{k}"/>' for k, v in sample.items() if isinstance(v, dict))
        types.append(f'<EntityType Name="{name}Type">{props}{navs}</EntityType>')
    entity_sets = "".join(f'<EntitySet Name="{n}" EntityType="{service}.{n}Type"/>' for n in sets)
    return (f'<?xml version="1.0" encoding="utf-8"?><edmx:Edmx Version="1.0" xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx"><edmx:DataServices>'
            f'<Schema Namespace="{service}">{"".join(types)}<EntityContainer Name="{service}_Entities">{entity_sets}</EntityContainer></Schema></edmx:DataServices></edmx:Edmx>')


def respond(entities: dict, password: str, method: str, path: str, params: dict, headers: dict) -> tuple[int, str, str]:
    """(status, body, content type) for one request; shared by the FastAPI route and the tests' httpx MockTransport."""
    if method != "GET":
        return 405, json.dumps({"error": {"message": {"value": "Read-only emulator"}}}), "application/json"
    auth = headers.get("authorization", "")
    ok = headers.get("apikey") == password if headers.get("apikey") else False
    if auth.lower().startswith("basic "):
        user, _, pw = base64.b64decode(auth[6:]).decode(errors="replace").partition(":")
        ok = secrets.compare_digest(user, USER) and secrets.compare_digest(pw, password)
    if not ok:
        return 401, json.dumps({"error": {"message": {"value": "Unauthorized"}}}), "application/json"
    if params.get("sap-client", CLIENT) != CLIENT:
        return 401, json.dumps({"error": {"message": {"value": f"Client {params.get('sap-client')} does not exist"}}}), "application/json"
    parts = path.strip("/").split("/")
    if len(parts) < 5 or parts[:4] != ["sap", "opu", "odata", "sap"] or parts[4] not in entities:
        return 404, json.dumps({"error": {"message": {"value": "Service not found"}}}), "application/json"
    service, rest = parts[4], parts[5:]
    if rest == ["$metadata"]:
        return 200, metadata_xml(service, entities[service]), "application/xml"
    if len(rest) != 1 or rest[0] not in entities[service]:
        return 404, json.dumps({"error": {"message": {"value": "Resource not found"}}}), "application/json"
    rows = entities[service][rest[0]]
    flt = params.get("$filter", "")
    if " eq " in flt:
        prop, _, value = flt.partition(" eq ")
        rows = [r for r in rows if str(r.get(prop.strip())) == value.strip().strip("'")]
    skip, top = int(params.get("$skip", 0)), int(params.get("$top", 100))
    expand = set(filter(None, params.get("$expand", "").split(",")))
    page = [{k: v for k, v in r.items() if not isinstance(v, dict) or k in expand} for r in rows[skip: skip + top]]
    return 200, json.dumps({"d": {"results": page}}), "application/json"


def router(snapshot_file: Path, password: str) -> APIRouter:
    r = APIRouter(include_in_schema=False)
    cache: dict[str, Any] = {}

    @r.get("/sap/opu/odata/sap/{path:path}")
    def odata(path: str, request: Request) -> Response:
        today = date.today().isoformat()
        if cache.get("day") != today:  # rebuilt daily so dates stay current
            cache.update(day=today, entities=build_entities(json.loads(Path(snapshot_file).read_text(encoding="utf-8"))))
        status, body, ctype = respond(cache["entities"], password, "GET", f"/sap/opu/odata/sap/{path}", dict(request.query_params),
                                      {k.lower(): v for k, v in request.headers.items()})
        return Response(body, status_code=status, media_type=ctype)

    return r
