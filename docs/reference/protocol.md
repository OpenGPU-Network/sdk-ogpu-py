# `ogpu.protocol`

1:1 wrappers around the OGPU contract ABIs. This is the layer that
actually talks to the chain — everything above it (`ogpu.client`,
`ogpu.agent`, `ogpu.events`) eventually funnels here.

The protocol layer exposes two parallel API styles:

1. **Instance classes** (`Source`, `Task`, `Response`, `Provider`,
   `Master`) — stateless live proxies bound to a single contract
   address. Clean for dashboards and any code that already holds a
   concept of "this task" or "this provider". Every method is a fresh
   RPC call; only `self.address` is persisted.
2. **Module functions** (`nexus`, `controller`, `terminal`, `vault`)
   — function-style wrappers on the four singleton contracts. Use
   when you want to do a single call without constructing an instance,
   or when iterating many addresses.

Every write function takes a `signer=` keyword argument that accepts
a hex private key string, an `eth_account.LocalAccount`, or `None`
(env-var fallback via `resolve_signer`). Vault operations have no
env-var fallback — they require explicit `signer=` to prevent
accidental cross-role transactions.

Revert decoding is handled uniformly by `TxExecutor`: every known
Solidity revert reason maps to a typed `OGPUError` subclass, and
unknown reverts fall through to a generic `TxRevertError(reason=...)`.
See [error handling](../guides/errors.md) for the full mapping.

---



## Instance classes

### Source

::: ogpu.protocol.source.Source
    options:
      show_root_heading: true
      heading_level: 4
      members:
        - __init__
        - load
        - get_client
        - get_status
        - get_params
        - get_metadata
        - get_task_count
        - get_tasks
        - get_registrant_count
        - get_registrants
        - get_registrant_id
        - get_preferred_environment_of
        - set_status
        - set_params
        - inactivate
        - snapshot

### Task

::: ogpu.protocol.task.Task
    options:
      show_root_heading: true
      heading_level: 4
      members:
        - __init__
        - load
        - get_source
        - get_status
        - get_params
        - get_metadata
        - get_payment
        - get_expiry_time
        - get_delivery_method
        - get_attempt_count
        - get_attempters
        - get_attempter_id
        - get_attempt_timestamps
        - get_response_of
        - get_responses
        - get_confirmed_response
        - get_winning_provider
        - is_already_submitted
        - cancel
        - snapshot

### Response

::: ogpu.protocol.response.Response
    options:
      show_root_heading: true
      heading_level: 4
      members:
        - __init__
        - load
        - get_task
        - get_params
        - get_data
        - fetch_data
        - get_status
        - get_timestamp
        - is_confirmed
        - confirm
        - snapshot

### Provider

::: ogpu.protocol.provider.Provider
    options:
      show_root_heading: true
      heading_level: 4
      members:
        - __init__
        - load
        - get_master
        - get_base_data
        - get_live_data
        - is_provider
        - get_default_agent_disabled
        - get_balance
        - get_lockup
        - get_unbonding
        - get_unbonding_timestamp
        - get_total_earnings
        - get_frozen_payment
        - get_sanction
        - is_eligible
        - is_whitelisted
        - announce_master
        - set_default_agent_disabled
        - register_to
        - unregister_from
        - attempt
        - stake
        - unstake
        - cancel_unbonding
        - claim_earnings
        - deposit_to_vault
        - withdraw_from_vault
        - snapshot

### Master

::: ogpu.protocol.master.Master
    options:
      show_root_heading: true
      heading_level: 4
      members:
        - __init__
        - load
        - get_provider
        - is_master
        - get_balance
        - get_lockup
        - get_unbonding
        - get_total_earnings
        - get_frozen_payment
        - is_eligible
        - is_whitelisted
        - announce_provider
        - remove_provider
        - remove_container
        - set_agent
        - stake
        - unstake
        - cancel_unbonding
        - claim_earnings
        - deposit_to_vault
        - withdraw_from_vault
        - snapshot

## Module-level functions

### `ogpu.protocol.nexus`

::: ogpu.protocol.nexus
    options:
      show_root_heading: false
      heading_level: 4
      members:
        - publish_source
        - update_source
        - inactivate_source
        - register
        - unregister
        - attempt

### `ogpu.protocol.controller`

::: ogpu.protocol.controller
    options:
      show_root_heading: false
      heading_level: 4
      members:
        - publish_task
        - confirm_response
        - cancel_task

### `ogpu.protocol.terminal`

::: ogpu.protocol.terminal
    options:
      show_root_heading: false
      heading_level: 4
      members:
        - set_agent
        - revoke_agent
        - announce_master
        - announce_provider
        - remove_provider
        - remove_container
        - set_default_agent_disabled
        - get_master_of
        - get_provider_of
        - get_base_data_of
        - get_live_data_of
        - is_master
        - is_provider
        - is_agent_of
        - is_default_agent_disabled

### `ogpu.protocol.vault`

::: ogpu.protocol.vault
    options:
      show_root_heading: false
      heading_level: 4
      members:
        - deposit
        - withdraw
        - lock
        - unbond
        - cancel_unbonding
        - claim
        - get_balance_of
        - get_lockup_of
        - get_unbonding_of
        - get_unbonding_timestamp
        - get_total_earnings_of
        - get_frozen_payment
        - get_sanction_of
        - is_eligible
        - is_whitelisted
        - get_min_lockup_per_source
        - get_unbonding_period

## Shared infrastructure

::: ogpu.protocol.TxExecutor
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.protocol.resolve_signer
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.protocol.load_contract
    options:
      show_root_heading: true
      heading_level: 3
