"""ERP / SAP integration layer: connectors (mock SAP snapshot, SAP OData), field mapping, staged synchronization, versioned
activation per customer, integration checks. Configured on the dashboard's ERP / SAP Setup page; every business service, the
Flowise tools and the LangGraph tools keep calling the same FastAPI endpoints, which resolve the customer's active snapshot."""
