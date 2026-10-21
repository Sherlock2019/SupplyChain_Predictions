# Synthetic SAP data

Loaded by `backend/scinsight/fixtures.py` at start-up. Loading is idempotent, and configured user keys replace previously
stored key hashes. Everything is fictional:
- Snapshot `SAP-SYN-2026-10-21T0600Z`, source system `S4HANA-SYNTHETIC`, as of **2026-10-21** (the business date).
- Random history uses seed 20261021.
- Every calculation records `provenance.synthetic = true`.

A snapshot older than 2 days, or no snapshot at all, makes every planning call return 409. The system never plans on stale data.

## Company: Belleva Cosmetics (tenant `scinsight-cosmetics`)

| Location | Name | Kind |
|---|---|---|
| FAC-1 | Lyon factory | factory |
| WH-A | Warehouse A, Paris | warehouse (target cover 14 days) |
| WH-B | Warehouse B, Madrid | warehouse |
| WH-C | Warehouse C, Milan | warehouse |

- **20 finished goods**, e.g.:
  - SER-VITC-30 Vitamin C serum 30 ml (pump bottle)
  - SUN-SPF50-100 Sunscreen SPF50 100 ml
  - CRM-HYDR-50 Hydrating cream
  - SER-RETI-30 Retinol serum
  - and 16 more
- **10 materials:** PUMP-DISP-24, BTL-GLS-30, SER-BASE-VC, CAP-PUMP-OVR, CRT-SER-30, TUB-SUN-100, SUN-BASE-50, JAR-CRM-50,
  CRM-BASE-HY, LBL-GEN.

| Supplier | Approved | Items (contract lead time) |
|---|---|---|
| SUP-A Alpine Dispensing | yes | PUMP-DISP-24 €0.42 (5 d), CAP-PUMP-OVR (5 d) |
| SUP-B Iberia Closures | yes | PUMP-DISP-24 €0.48 (7 d), CAP-PUMP-OVR (7 d) |
| SUP-C Nordic Glassworks | yes | BTL-GLS-30 (14 d) |
| SUP-D ChemBase Labs | yes | SER-BASE-VC, SUN-BASE-50, CRM-BASE-HY (10 d) |
| SUP-E PackPrint Europe | yes | CRT-SER-30, LBL-GEN, JAR-CRM-50 |
| SUP-F TubeTech | yes | TUB-SUN-100 (9 d) |
| SUP-X Unvetted Pumps Ltd | **no** | PUMP-DISP-24 €0.30 (4 d): cheapest and fastest, but never recommended (POL-PROC-001) |

**Transport lanes:** road between all warehouses. For example WH-C→WH-B takes 2 days and costs €0.35/unit + €120, with
capacity 5,000. Factory→warehouse lanes take 1–2 days.

**History:**
- About 60 historical goods receipts.
- SUP-A pumps really take 8–9 days, against a 5-day contract.
- 90 days of daily sales per SKU and warehouse.

A second tenant, `northwind-pharma`, exists only to prove isolation: it has its own warehouse WH-X and its own confidential document.

## The three scenarios in the data

### 1. Serum launch: 50,000 bottles, 20,000 pumps missing
- PRD-1001 asks for SER-VITC-30 × 50,000 at FAC-1, starting 2026-10-27. BOM v2 is approved; v3 is a draft and v1 has expired.
- BOM v2 lines: PUMP-DISP-24 1 EA, BTL-GLS-30 1 EA (+0.5 % scrap), SER-BASE-VC 0.031 KG (+2 % scrap), CAP-PUMP-OVR, CRT-SER-30.
- Pump stock:
  - P-REL-01: 20,000 released
  - P-REL-02: 10,000 released
  - P-BLK-03: 4,000 **QA blocked**, so excluded
  - Usable: 30,000. **Missing: 20,000.**
- Open purchase orders:
  - PO-4500021001: 25,000 confirmed, but promised 2026-11-05 (late)
  - PO-4500021002: 8,000, status open (unconfirmed, so not counted)
- **Result:** produce 30,000 now. Purchase 20,000 from SUP-A, arriving 2026-10-30 on the demonstrated 9-day lead time (€8,400),
  or move the start to 2026-10-30. SUP-X is infeasible because it is not approved.

### 2. Sunscreen at Warehouse B: 6 days of cover
- WH-B: 1,200 usable at 200.25 units/day, so 6.0 days of cover; stock-out on 2026-10-27.
- WH-A: 3,600 (29.8 days). WH-C: 4,500 usable (40.9 days).
- **Result:** transfer **2,004** from WH-C (donor keeps 14 days), arriving 2026-10-23, costing €821.40.
  - WH-A could only cover part of the need (1,906 of 2,205).
  - PRD-1002's output lands on 2026-11-13, too late.

### 3. Expiry and quality exclusions at Warehouse C
| Batch | Qty | Status | Usable? |
|---|---|---|---|
| S-C-01 | 3,000 | released, expires 2027-06-30 | yes; the only transferable batch |
| S-C-02 | 1,500 | released, expires 2026-11-10 | yes locally; not transferable (18 days of shelf life on arrival, less than 60) |
| S-C-03 | 800 | expired 2026-10-15 | no; proposed for destruction review |
| S-C-04 | 700 | QA blocked | no |
| S-C-05 | 1,000 | reserved for SO-88001 | no |
| S-C-06 | 500 | in quality inspection | no |

On hand 7,500, **usable 4,500**.

### Learning case
- REC-HIST-0001 (executed) ordered 25,000 pumps from SUP-A with a predicted lead time of **5 days**. The procurement manager approved it.
- SAP execution was recorded as PO-4500020950: ordered 2026-09-30, received 2026-10-09, so **9 days**.
- Reconciliation gives a signed error of **+4 days**.
