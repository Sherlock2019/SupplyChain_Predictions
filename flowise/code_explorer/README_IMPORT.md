# SCInsight Functions & Code Explorer — Flowise import

Eight **documentation** Agentflows (Flowise 3.1.2), category "SCInsight Code Explorer":

| Flow | Export |
|---|---|
| SCInsight — Functions & Code Explorer (master: categories + 3 real execution paths) | `00_master.json` |
| SCInsight Code Explorer · 01 FastAPI | `01_fastapi.json` |
| SCInsight Code Explorer · 02 Business logic | `02_business_logic.json` |
| SCInsight Code Explorer · 03 SAP / data | `03_sap_data.json` |
| SCInsight Code Explorer · 04 AI / ML | `04_ai_ml.json` |
| SCInsight Code Explorer · 05 Security & governance | `05_security_governance.json` |
| SCInsight Code Explorer · 06 Testing | `06_testing.json` |
| SCInsight Code Explorer · 07 Flowise | `07_flowise_functions.json` |

How to read a canvas: one column per source file; each **Custom Function node** is one real function (open it: id, file and lines,
summary, route, callers, callees). The **Sticky Note** to its right holds the complete annotated source. Edges are the verified relations
from `code_explorer/registry/dependencies.json` (calls function, HTTP request, validates input, Depends). The node JavaScript is only a
comment plus `return "<id>"`: running a code-map flow never executes Python or calls the backend.

## Import

Automatic (creates or updates only these eight flows by name):

```bash
python3 code_explorer/tools/build_code_explorer.py
python3 flowise/code_explorer/deploy_code_map.py build
python3 flowise/code_explorer/deploy_code_map.py import --flowise-url http://127.0.0.1:3101
```

Manual: Flowise → Agentflows → Add New → ⚙ → Load Agents → pick one of the JSON files → Save.

`imported.json` lists the flow ids and canvas URLs of the last import (read back and checked against the export).
