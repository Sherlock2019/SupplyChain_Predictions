# LP-03 — Inter-warehouse transfer policy

## Network

Stock balancing covers DC01 (Paris), DC21 (Dubai), and DC22 (Singapore). Lanes and costs: DC01→DC21 3 days EUR 0.70/unit, DC01→DC22 5 days EUR 0.92/unit, DC21→DC22 4 days EUR 0.61/unit, and the reverse lanes at similar cost.

## Rules

A source warehouse may transfer only inventory above its forecast demand and safety target. The optimization objective minimises transport cost while preserving the target service level. Transfer recommendations do not create SAP stock-transfer orders.

## Delays

In-transit shipments delayed more than three days must be escalated to the logistics control tower and considered when proposing new transfers to the same destination.
