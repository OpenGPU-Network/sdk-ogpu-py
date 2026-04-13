---
title: OpenGPU Python SDK
hide:
  - navigation
  - toc
---

# OpenGPU Python SDK

Python client for the **OpenGPU Network** — publish AI tasks, run sources,
pay providers, monitor on-chain state.

<p style="font-size: 1.1em; color: var(--md-default-fg-color--light);">
Object-oriented contract instances. Typed errors. Chain-only — no
management-backend dependency. Works on mainnet and testnet out of the box.
</p>

```python
from ogpu import ChainConfig, ChainId
from ogpu.client import publish_task, TaskInfo, TaskInput

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

task = publish_task(TaskInfo(
    source="0x...",
    config=TaskInput(function_name="predict", data={"prompt": "hello"}),
    expiryTime=int(time.time()) + 3600,
    payment=Web3.to_wei(0.01, "ether"),
))

print(task.address)           # live Task instance
print(task.get_status())      # TaskStatus.NEW
print(task.get_source())      # navigate back to Source
```

---

<div class="grid cards" markdown>

-   :material-rocket-launch-outline: **Get Started**

    ---

    Install, publish your first task, watch it finalize.

    [:octicons-arrow-right-24: Quickstart](getting-started/quickstart.md)

-   :material-book-open-variant: **Guides**

    ---

    Task-oriented how-tos: publishing, reading state, vault, events, agents.

    [:octicons-arrow-right-24: All guides](guides/publishing.md)

-   :material-code-braces: **Reference**

    ---

    Full API reference generated from source. Every method, every parameter.

    [:octicons-arrow-right-24: API reference](reference/client.md)

-   :material-layers-triple: **Architecture**

    ---

    Layered by role: `chain` → `types` → `protocol` → `client` / `agent` / `events`.

    [:octicons-arrow-right-24: Concepts](getting-started/concepts.md)

</div>

---

## What's in the SDK

=== "Client operations"

    ```python
    from ogpu.client import (
        publish_source, publish_task, confirm_response,
        cancel_task, update_source, inactivate_source,
        set_agent, get_task_responses,
    )
    ```

    Everything you need to publish and manage tasks as a client.
    Uses `CLIENT_PRIVATE_KEY` env var for signing by default.

=== "Instance classes"

    ```python
    from ogpu.protocol import Source, Task, Response, Provider, Master

    task = Task.load("0x...")          # eager validation
    task.get_status()                   # TaskStatus
    task.get_attempters()               # list[str]
    task.get_confirmed_response()       # Response | None
    task.snapshot()                     # frozen capture of every field
    ```

    Stateless live proxies — every method hits the chain fresh.

=== "Vault"

    ```python
    from ogpu.protocol import vault

    vault.deposit("0x...", amount=10**18, signer=key)
    vault.lock(amount=5 * 10**17, signer=key)
    vault.get_balance_of("0x...")
    vault.get_lockup_of("0x...")
    ```

    Full vault lifecycle: deposit, lock, unbond, claim.

=== "Events (async)"

    ```python
    import asyncio
    from ogpu.events import watch_attempted

    async def monitor(task_addr: str):
        async for event in watch_attempted(task_addr):
            print(f"Attempt from {event.provider}")

    asyncio.run(monitor("0x..."))
    ```

    Six `watch_*` generators for the critical Nexus events. The one async
    island — the rest of the SDK is sync.

---

## Modules at a glance

| Module | Purpose |
|---|---|
| [`ogpu.chain`](reference/chain.md) | `ChainConfig`, `ChainId`, RPC, nonce utilities, ABI loader |
| [`ogpu.types`](reference/types.md) | Enums, exception hierarchy, `Receipt`, metadata dataclasses |
| [`ogpu.protocol`](reference/protocol.md) | Low-level contract wrappers + instance classes |
| [`ogpu.client`](reference/client.md) | Client-role high-level workflows |
| [`ogpu.agent`](reference/agent.md) | Agent scheduler wrappers (register / attempt) |
| [`ogpu.events`](reference/events.md) | Async event watchers |
| [`ogpu.ipfs`](reference/ipfs.md) | Publish and fetch off-chain content |
| [`ogpu.service`](reference/service.md) | Framework for source developers (Docker side) |

---

## Chain-only by design

The SDK talks to **one thing**: the OpenGPU RPC node. There is no indexer
wrapper, no management-backend dependency, no fallback HTTP path. Every
`get_*` method hits JSON-RPC. Users who need aggregate cross-task queries
call the management backend API directly — it is not the SDK's business.

!!! info "Versioning"
    v0.2.1 is an SDK-only release. Contract addresses and ABIs are
    unchanged from the v0.2 protocol. See the
    [changelog](about/changelog.md) for the full breaking-change list.
