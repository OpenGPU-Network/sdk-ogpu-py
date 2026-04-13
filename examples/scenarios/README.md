# Scenarios

End-to-end reference flows. Each notebook walks through a real multi-step usage pattern
with markdown narrative, code, and last-run outputs committed alongside so you can see
what the SDK actually returns without running anything.

These are **reference material**, not a pytest suite. Read them top to bottom, copy the
cells you need into your own code, and adapt.

## Prerequisites

Open a notebook with Jupyter or VS Code:

```bash
pip install ogpu[examples]
jupyter notebook examples/scenarios/
```

Each scenario lists the specific environment variables it expects
(`CLIENT_PRIVATE_KEY`, `MASTER_PRIVATE_KEY`, `AGENT_PRIVATE_KEY`, `VAULT_ACTOR_KEY`,
`MASTER_ADDR`, `PROVIDER_ADDR`). All scenarios target OGPU testnet.

Master–provider pairing (the Provider App's job) is **not** covered here — scenarios 06
and 07 assume it has already been done.

## Scenarios

| # | Notebook | Role(s) | Highlights |
|---|---|---|---|
| 01 | [01_client_happy_path.ipynb](01_client_happy_path.ipynb) | Client | publish_source → publish_task → watch_attempted → confirm → FINALIZED |
| 02 | [02_task_cancellation.ipynb](02_task_cancellation.ipynb) | Client | publish_task → cancel → verify revert on double-cancel |
| 03 | [03_source_update.ipynb](03_source_update.ipynb) | Client | set_params flipping minPayment on-chain |
| 04 | [04_source_inactivation.ipynb](04_source_inactivation.ipynb) | Client | inactivate → publish_task reverts |
| 05 | [05_vault_lifecycle.ipynb](05_vault_lifecycle.ipynb) | Any | deposit → lock → unbond → wait → claim |
| 06 | [06_agent_setup.ipynb](06_agent_setup.ipynb) | Master | set_agent + is_agent_of + revoke_agent (authorizes The Order) |
| 07 | [07_agent_driven_flow.ipynb](07_agent_driven_flow.ipynb) | Client + Agent (for Master) | Agent key drives register/attempt up to Task ATTEMPTED — response submission lives in the docker source runtime, not the SDK |

## Agent flow (scenarios 06 + 07)

Scenario 06 shows a master authorizing an agent address (e.g. The Order
`0x306Dc3fF30254675B209D916475094401aCC4a1E`) via `Terminal.setAgent`. Once set,
the agent's own key can sign `Nexus.register` / `Nexus.attempt` calls on behalf
of any provider managed by that master. Response submission (`Nexus.submitResponse`)
is intentionally **not** in the SDK and must come from the docker source runtime
that produced the actual compute output.

Scenario 07 picks up where 06 leaves off: a client publishes a source and task,
and the agent key drives the full provider-side lifecycle (register, attempt,
submit) without the master ever signing a task-related transaction. This is
the pattern external schedulers like The Order use at scale.

**Note:** Scenario 07 submits a **fake response payload**. It does not execute a
docker source — that's the Provider App's job. The notebook exercises only the
SDK's on-chain orchestration via agent delegation.
