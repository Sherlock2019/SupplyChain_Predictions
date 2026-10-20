-- Local Compose bootstrap. Cloud databases (RDS / Cloud SQL) are prepared by scripts/db-bootstrap.sh with the same statements.
-- One database per component: governance ledger + RAG + LangGraph checkpoints, Flowise, Langfuse.
CREATE EXTENSION IF NOT EXISTS vector;
SELECT 'CREATE DATABASE flowise' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'flowise')\gexec
SELECT 'CREATE DATABASE langfuse' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langfuse')\gexec
