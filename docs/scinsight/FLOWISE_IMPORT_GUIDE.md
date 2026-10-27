# Flowise import guide

Tested with **Flowise 3.1.2**, both in the stack's instance and in a brand-new empty instance (see [TEST_RESULTS.md](TEST_RESULTS.md)).

## Prerequisites

1. **The SCInsight API is reachable from the Flowise container**, e.g. `http://api:8000/scinsight` on the same Docker network.
2. **SSRF policy.** Flowise's default policy denies every private range, including the Docker bridge, so the tools would fail
   with `isDeniedIP … denied by policy`. Set exactly what the stack sets:
   ```
   HTTP_SECURITY_CHECK=false          # replaces the built-in list with HTTP_DENY_LIST (it does not disable the check)
   HTTP_DENY_LIST=0.0.0.0,10.0.0.0/8,127.0.0.0/8,169.254.0.0/16,192.168.0.0/16,224.0.0.0/4,240.0.0.0/4,255.255.255.255/32,::1,fc00::/7,fe80::/10,fd00:ec2::254,ff00::/8
   ```
3. **An OpenAI-compatible LLM endpoint** reachable from Flowise. Locally this is Qwen 2.5 7B via Ollama at
   `http://host.docker.internal:11435/v1`.
4. **`.env`** with `FLOWISE_ADMIN_EMAIL` / `FLOWISE_ADMIN_PASSWORD`, `SCI_AGENT_KEY`, `QWEN_MODEL`, `QWEN_BASE_URL` and `QWEN_API_KEY`.

## Automated import (recommended)

```bash
python3 flowise/scinsight/deploy.py import                                   # the stack's Flowise (127.0.0.1:3000)
python3 flowise/scinsight/deploy.py import --flowise-url http://host:3010 \
        --flowise-internal-url http://<flowise-container>:3000 --state-file deploy-evidence/other.json
```

The importer reads only the committed export files listed in `flowise/scinsight/manifest.json`. Order:

1. Register or log in the admin. Create the API key `scinsight-flows` (permissions: chatflows, agentflows, tools, variables,
   credentials, executions).
2. Set the Flowise Variables `sci_api_url` and `sci_agent_key` (values are never printed).
3. Set the credentials `scinsight-qwen` (openAIApi) and `scinsight-flowise-api` (chatflowApi, used by Execute Flow).
4. Upsert the **14 Custom Tools**, by name.
5. Import the **7 specialist Agentflows**, then the **supervisor** (it references the specialists' ids), then the **Chatflow**
   (with its post-processing config). Every flow is protected by the API key.
6. Write `FLOWISE_SCI_API_KEY`, `FLOWISE_SCI_CHATFLOW_ID` and `FLOWISE_SCI_SUPERVISOR_ID` to `.env`, or to `--state-file`.

The importer upserts by name, so re-running it updates in place.

### Placeholders bound at import

| Placeholder | Bound to |
|---|---|
| `__QWEN_CREDENTIAL__` | id of credential `scinsight-qwen` |
| `__QWEN_MODEL__`, `__QWEN_BASE_URL__` | `.env` or `--qwen-model` / `--qwen-base-url` |
| `__FLOWISE_API_CREDENTIAL__` | id of credential `scinsight-flowise-api` |
| `__FLOWISE_INTERNAL_URL__` | `--flowise-internal-url` (default `http://flowise:3000`); loopback is denied by the SSRF policy, so it must be the container name |
| `__TOOL:<name>__` | id of the imported Custom Tool |
| `__FLOW:<name>__` | id of the imported specialist Agentflow |

## Manual import through the Flowise UI

The exports are plain flowData (`{nodes, edges}`), the format the UI's *Load* expects.

1. **Variables:** create `sci_api_url` = `http://api:8000/scinsight` and `sci_agent_key` = the value of `SCI_AGENT_KEY`.
2. **Credentials:** create an *OpenAI API* credential for the LLM. Create a *Chatflow API* credential holding a Flowise API key.
3. **Tools:** for each file in `flowise/tools/`, go to Tools → *Load* and select it.
4. **Agentflows:** load the 7 specialists first. Then load the supervisor and, in each of its 7 *Execute Flow* nodes, select the
   matching specialist, the Chatflow API credential, and the Base URL `http://flowise:3000`.
5. **LLM nodes:** in every LLM node, select your OpenAI credential and set the model name and base path.
6. **Chatflow:** load it. In each of the 14 Custom Tool nodes, select the tool with the same name. Under *Configuration →
   Post Processing*, enable it and paste `flowise/chatflows/SCInsight-Cosmetics-Chatflow-v1.postprocessing.js`.
7. Under *Configuration → Security*, assign an API key to all 9 flows.

The automated importer does exactly these steps.

## Clean-instance test (definition of done)

```bash
bash scripts/scinsight-clean-flowise-test.sh         # new empty Flowise on :3010 → import exports → run the e2e tests there
bash scripts/scinsight-clean-flowise-test.sh --down  # remove it
```

## Re-generating the exports

```bash
python3 flowise/scinsight/deploy.py build   # runs build-scinsight.cjs inside the Flowise container (node definitions of that version)
```

Never hand-edit the JSON. Change `flowise/scinsight/build-scinsight.cjs`, then build and import again.
