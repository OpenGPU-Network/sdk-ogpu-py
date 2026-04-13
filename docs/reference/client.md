# `ogpu.client`

Client-role workflow layer. These functions are the top-level entry
points most application code uses — publish a source, publish a task,
confirm a response, cancel a task. Internally they build the on-chain
parameter tuples, upload metadata to IPFS when needed, and delegate to
the protocol layer.

Every call accepts a `private_key=` keyword. When omitted, the SDK
reads the `CLIENT_PRIVATE_KEY` environment variable; if that's not set
either, you get a typed `MissingSignerError`. You can also pass an
`eth_account.LocalAccount` as `private_key=` to use hardware wallets
or KMS signers.

Publishing functions (`publish_source`, `publish_task`) return **live
instance classes** — `Source` and `Task` — not string addresses. Every
method on the returned instance hits the chain fresh, so you can
inspect state right after publishing without a round-trip through
your own code. See [reading state](../guides/reading-state.md) for the
full instance-class API.

State-changing functions return typed `Receipt` dataclasses (for
`cancel_task`, `update_source`, `inactivate_source`) or hex tx-hash
strings (for `confirm_response`, `set_agent`). This inconsistency is
historical — future versions will unify on `Receipt`.

---



## Publishing

::: ogpu.client.publish_source
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.client.publish_task
    options:
      show_root_heading: true
      heading_level: 3

## Response operations

::: ogpu.client.get_task_responses
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.client.confirm_response
    options:
      show_root_heading: true
      heading_level: 3

## Task operations

::: ogpu.client.cancel_task
    options:
      show_root_heading: true
      heading_level: 3

## Source operations

::: ogpu.client.update_source
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.client.inactivate_source
    options:
      show_root_heading: true
      heading_level: 3

## Agent

::: ogpu.client.set_agent
    options:
      show_root_heading: true
      heading_level: 3
