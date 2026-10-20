"""Deep Agents supplier-continuity research harness.

Planning (write_todos), a virtual scratch filesystem for working notes, and delegation to three focused subagents.
Every tool is read-only and goes through the governed gateway; the agent can recommend but never act.
"""
from __future__ import annotations

from deepagents import create_deep_agent

from backend.app.config import get_settings
from backend.app.llm import GROUNDING_RULES, chat_model
from backend.app.observability import langfuse_callbacks
from backend.app.tools import (
    factory_material_readiness,
    logistics_status,
    quality_status,
    sap_snapshot,
    search_governed_knowledge,
    supplier_risk,
)

SYSTEM_PROMPT = (
    GROUNDING_RULES
    + "\n\nYou are the supplier-continuity research agent. For each request:\n"
    "1. Write a short todo plan.\n"
    "2. Call supplier_risk for the supplier to get the deterministic scorecard.\n"
    "3. Delegate contract terms to the contract-analyst and quality evidence to the quality-analyst; use the logistics-analyst only "
    "when shipments matter.\n"
    "4. Finish with a report in markdown: Risk rating, Evidence (cite analysis_id, PO numbers, inspection lots, document titles), "
    "Contract levers (lead time, expedite clause, secondary source), Recommended advisory actions, Approvals required.\n"
    "Never claim an action was executed."
)

SUBAGENTS = [
    {
        "name": "contract-analyst",
        "description": "Finds contractual lead time, OTIF target, expedite clause, penalties and secondary-source terms for one supplier.",
        "system_prompt": GROUNDING_RULES + "\nSearch the governed knowledge base (category contract) and return exact clauses with document titles.",
        "tools": [search_governed_knowledge],
    },
    {
        "name": "quality-analyst",
        "description": "Assesses inspection lots, rejected/blocked batches and quality policy for a supplier's materials.",
        "system_prompt": GROUNDING_RULES + "\nUse quality_status and quality policies. Report lot numbers, quantities, defects and release dates.",
        "tools": [quality_status, search_governed_knowledge],
    },
    {
        "name": "logistics-analyst",
        "description": "Checks inbound shipments, delays and carrier SLAs affecting a supplier's deliveries.",
        "system_prompt": GROUNDING_RULES + "\nUse logistics_status and logistics policies. Report shipment ids, delays and revised ETAs.",
        "tools": [logistics_status, search_governed_knowledge],
    },
]


def build_deep_agent(checkpointer=None):
    settings = get_settings()
    agent = create_deep_agent(
        model=chat_model(settings, max_tokens=1500),
        tools=[supplier_risk, sap_snapshot, search_governed_knowledge, quality_status, logistics_status, factory_material_readiness],
        system_prompt=SYSTEM_PROMPT,
        subagents=SUBAGENTS,
        checkpointer=checkpointer,
        name="supplier_deep_agent",
    )
    callbacks = langfuse_callbacks()
    return agent.with_config({"callbacks": callbacks, "recursion_limit": 60}) if callbacks else agent.with_config({"recursion_limit": 60})


graph = build_deep_agent()
