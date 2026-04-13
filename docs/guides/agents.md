# Agents

An **agent** is an address authorized by a master or client via
`Terminal.setAgent(agent, true)`. Once authorized, the agent's own key
can sign Nexus operations on the principal's behalf — without the
principal ever having to touch the transaction.

The typical use case is a **scheduler**: a single agent service that
watches for new tasks, assigns them to providers managed by a master,
and submits attempts and responses. The Order is OpenGPU's built-in
scheduler and lives at
`0x306Dc3fF30254675B209D916475094401aCC4a1E`.

## Authorizing an agent

Only clients and masters can set agents — providers cannot (the
`Terminal.AgentSet` event is only triggered by client or master keys).

```python
from ogpu.protocol import terminal

# Master authorizes The Order
receipt = terminal.set_agent(
    "0x306Dc3fF30254675B209D916475094401aCC4a1E",
    True,
    signer=MASTER_KEY,
)

# Verify
assert terminal.is_agent_of(MASTER_ADDR, "0x306Dc3fF...")
```

Or via the `Master` instance:

```python
from ogpu.protocol import Master

master = Master(MASTER_ADDR)
master.set_agent("0x306Dc3fF...", True, signer=MASTER_KEY)
```

## Revoking

```python
terminal.revoke_agent("0x306Dc3fF...", signer=MASTER_KEY)
# or
terminal.set_agent("0x306Dc3fF...", False, signer=MASTER_KEY)
```

Both do the same thing. `revoke_agent` is a one-line convenience.

## Acting as an agent: `ogpu.agent`

Once an agent is authorized, the agent's own process uses the
`ogpu.agent` package to drive Nexus calls with its own key. The
protocol's `isAgentOf(principal, msg.sender)` check authorizes the
operation.

```python
from ogpu import agent

# Agent registers a provider to a source
agent.register_to(
    source="0xSOURCE",
    provider="0xPROVIDER",
    env=1,
    # signer=... falls back to AGENT_PRIVATE_KEY env var
)

# Agent submits an attempt
agent.attempt(
    task="0xTASK",
    provider="0xPROVIDER",
    suggested_payment=Web3.to_wei(0.01, "ether"),
)

# Agent unregisters a stale provider
agent.unregister_from(
    source="0xSOURCE",
    provider="0xPROVIDER",
)
```

### Why no `submit_response`?

The agent is a **scheduler role** — it picks which providers attempt
which tasks. It does not produce response content. Response payloads
come from a real compute run (the docker source executing the handler)
and must be signed by the provider whose image produced them.
`submit_response` is not exposed in `ogpu.agent` — and not in the
broader SDK either. It only lives inside the docker source runtime,
otherwise providers could fabricate responses without doing real work.

### Why no `setBaseData` / `setLiveData`?

These Terminal functions use `msg.sender` to identify whose data is
being set, so an agent can't use them on behalf of another provider.
For the same reason, the SDK does not expose them at all — provider
self-reported state must come from the running provider runtime, not
from an SDK script.

## Environment variable

`ogpu.agent` reads `AGENT_PRIVATE_KEY` when `private_key` (or `signer`)
is omitted:

```bash
export AGENT_PRIVATE_KEY=0xTHE_ORDER_OR_YOUR_SCHEDULER_KEY
```

```python
from ogpu import agent
agent.register_to("0xSRC", "0xPROV", 1)   # uses AGENT_PRIVATE_KEY
```

Or pass explicitly:

```python
agent.register_to("0xSRC", "0xPROV", 1, private_key="0x...")
```

## Client-side agents

A **client** can also authorize an agent to act on their behalf for
publishing tasks and confirming responses. Same `Terminal.setAgent`
call, same `AGENT_PRIVATE_KEY` env var — but the operations available
to a client-authorized agent are client-side (publish_task,
confirm_response) rather than scheduler-side (register, attempt).

```python
# Client sets agent
terminal.set_agent("0xAGENT_ADDR", True, signer=CLIENT_KEY)

# Agent now signs client-side calls
from ogpu.protocol import controller
controller.publish_task(params, signer=AGENT_KEY)
```

## End-to-end example

```python
from ogpu.protocol import terminal
from ogpu import agent

MASTER_KEY = "0x..."
MASTER_ADDR = "0x..."
SCHEDULER_KEY = "0x..."
SCHEDULER_ADDR = "0x..."
PROVIDER_ADDR = "0x..."
SOURCE_ADDR = "0x..."
TASK_ADDR = "0x..."

# 1. Master authorizes the scheduler once, at provisioning time
terminal.set_agent(SCHEDULER_ADDR, True, signer=MASTER_KEY)
assert terminal.is_agent_of(MASTER_ADDR, SCHEDULER_ADDR)

# 2. Scheduler process watches for new tasks
from ogpu.events import watch_task_published

import asyncio
async def loop():
    async for event in watch_task_published(SOURCE_ADDR):
        # 3. Scheduler decides which provider gets this task
        agent.register_to(SOURCE_ADDR, PROVIDER_ADDR, env=1, private_key=SCHEDULER_KEY)
        agent.attempt(event.task, PROVIDER_ADDR, 10**16, private_key=SCHEDULER_KEY)
        # 4. Provider's docker source actually runs and submits — not the agent

asyncio.run(loop())
```

## Next

- [Events](events.md) — the async watchers a scheduler uses
- [Publishing](publishing.md) — the client-side flow that creates the tasks
- [API reference: ogpu.agent](../reference/agent.md)
