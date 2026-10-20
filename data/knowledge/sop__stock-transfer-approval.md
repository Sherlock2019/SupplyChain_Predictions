# SOP SC-211 — Regional stock balancing and transfer approval

## Scope

Applies to finished goods held at DC01 (Paris Central), DC21 (Dubai Travel Retail), and DC22 (Singapore APAC).

## Target stock

Target stock per warehouse equals forecast demand over the review horizon (default 14 days) adjusted for the service level, plus material safety stock. Forecasts come from the approved XGBoost demand model; the optimizer is OR-Tools linear programming minimising transport cost plus a heavy penalty for unresolved shortages.

## Transfer rules

A source warehouse may only ship stock above its own target. Air freight is allowed only for high-priority travel-retail orders. Each proposed transfer must show quantity, lane, lead time, cost, and carbon estimate.

## Approval matrix

Transfers below EUR 5,000 estimated cost need supply-chain manager approval. Transfers above EUR 5,000 additionally require the regional logistics director. After approval, a planner creates the SAP stock-transport order manually. Rejected recommendations are retained in the audit log with the manager's comment.
