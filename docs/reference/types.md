# `ogpu.types`

Pure data types shared across the whole SDK — enums, exceptions,
`Receipt`, metadata and snapshot dataclasses. This package is a **leaf**
in the dependency graph: nothing here imports from `ogpu.protocol`,
`ogpu.client`, `ogpu.chain`, or any other higher layer. Every type is
a plain Python data container with no network I/O, no chain access,
and no hidden side effects.

What you'll find here:

- **Enums** — typed versions of the `uint8` fields returned by the
  contracts (`TaskStatus`, `SourceStatus`, `ResponseStatus`,
  `Environment`, `DeliveryMethod`, `Role`).
- **Errors** — the full `OGPUError` hierarchy, 30 concrete classes
  grouped into seven abstract domains. See
  [error handling](../guides/errors.md) for usage patterns.
- **`Receipt`** — frozen dataclass returned by every write operation.
- **Metadata dataclasses** — `SourceInfo`, `TaskInfo`, `TaskInput`,
  `SourceMetadata`, `ImageEnvironments`, plus on-chain struct mirrors
  (`SourceParams`, `TaskParams`, `ResponseParams`) and snapshot types
  (`SourceSnapshot`, `TaskSnapshot`, etc.).

---



## Enums

### TaskStatus

::: ogpu.types.enums.TaskStatus
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### SourceStatus

::: ogpu.types.enums.SourceStatus
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### ResponseStatus

::: ogpu.types.enums.ResponseStatus
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### Environment

::: ogpu.types.enums.Environment
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### DeliveryMethod

::: ogpu.types.enums.DeliveryMethod
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### Role

::: ogpu.types.enums.Role
    options:
      show_root_heading: true
      heading_level: 4
      members: []

## Receipt

::: ogpu.types.receipt.Receipt
    options:
      show_root_heading: true
      heading_level: 3
      members:
        - tx_hash
        - block_number
        - gas_used
        - status
        - logs
        - timestamp
        - from_web3_receipt

## Metadata

### SourceInfo

::: ogpu.types.metadata.SourceInfo
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### TaskInfo

::: ogpu.types.metadata.TaskInfo
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### TaskInput

::: ogpu.types.metadata.TaskInput
    options:
      show_root_heading: true
      heading_level: 4

### SourceMetadata

::: ogpu.types.metadata.SourceMetadata
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### ImageEnvironments

::: ogpu.types.metadata.ImageEnvironments
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### SourceParams

::: ogpu.types.metadata.SourceParams
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### TaskParams

::: ogpu.types.metadata.TaskParams
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### ResponseParams

::: ogpu.types.metadata.ResponseParams
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### Snapshot dataclasses

::: ogpu.types.metadata.SourceSnapshot
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.metadata.TaskSnapshot
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.metadata.ResponseSnapshot
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.metadata.ProviderSnapshot
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.metadata.MasterSnapshot
    options:
      show_root_heading: true
      heading_level: 4
      members: []

## Errors

Every SDK exception inherits from `OGPUError`. See
[error handling](../guides/errors.md) for the full hierarchy and usage.

### Base

::: ogpu.types.errors.OGPUError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### Abstract domain bases

::: ogpu.types.errors.NotFoundError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.errors.StateError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.errors.PermissionError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.errors.VaultError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.errors.TxError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.errors.ConfigError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

::: ogpu.types.errors.IPFSError
    options:
      show_root_heading: true
      heading_level: 4
      members: []

### Concrete errors

::: ogpu.types.errors
    options:
      show_root_heading: false
      heading_level: 4
      members:
        - TaskNotFoundError
        - SourceNotFoundError
        - ResponseNotFoundError
        - ProviderNotFoundError
        - MasterNotFoundError
        - TaskExpiredError
        - TaskAlreadyFinalizedError
        - ResponseAlreadyConfirmedError
        - SourceInactiveError
        - NotTaskOwnerError
        - NotSourceOwnerError
        - NotMasterError
        - NotProviderError
        - InsufficientBalanceError
        - InsufficientLockupError
        - UnbondingPeriodNotElapsedError
        - NotEligibleError
        - TxRevertError
        - NonceError
        - GasError
        - InvalidRpcUrlError
        - MissingSignerError
        - InvalidSignerError
        - ChainNotSupportedError
        - IPFSFetchError
        - IPFSGatewayError
