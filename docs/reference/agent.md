# `ogpu.agent`

High-level wrappers for the **agent scheduler role**. An agent is an
address authorized via `Terminal.setAgent(agent, True)` by a master
or client — once authorized, the agent's own key can sign Nexus
operations on the principal's behalf. The protocol checks
`isAgentOf(principal, msg.sender)` to authorize each call.

The typical use case is a **scheduler service**: a single long-running
process (e.g. The Order, OpenGPU's built-in scheduler at
`0x306Dc3fF30254675B209D916475094401aCC4a1E`) that watches for new
tasks and dispatches them to providers managed by a given master —
without the master ever having to sign each transaction.

Every function reads `AGENT_PRIVATE_KEY` from the environment when
`private_key` is omitted. See the [agents guide](../guides/agents.md)
for the full end-to-end flow including how to set up the agent on
the master side first.

!!! info "Scheduler role, not response producer"
    `submit_response` is not exposed here, and not anywhere else in
    the SDK either. Agents schedule work (register / attempt /
    unregister) — they do not produce response content. Response
    payloads come from a real compute run (the docker source executing
    its handler) and must be signed by the provider whose image
    produced them, otherwise providers could spoof responses from
    arbitrary scripts.

!!! info "No `setBaseData` / `setLiveData`"
    Provider self-reported state writes use `msg.sender` and must come
    from the provider's own runtime. Like `submit_response`, they're
    not in `ogpu.agent` and not in `ogpu.protocol.terminal` either —
    self-reported state from random SDK callers would defeat the point
    of the field.

---



::: ogpu.agent.register_to
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.agent.unregister_from
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.agent.attempt
    options:
      show_root_heading: true
      heading_level: 3
