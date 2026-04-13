# `ogpu.service`

Framework used inside **source developer** docker containers to expose
handler functions as network-callable task endpoints. This module is
conceptually separate from the rest of the SDK — the blockchain-facing
packages (`ogpu.chain`, `ogpu.protocol`, `ogpu.client`, `ogpu.agent`,
`ogpu.events`, `ogpu.ipfs`) are for interacting with on-chain state,
while `ogpu.service` is for the other side of the protocol: running the
actual task handlers that providers execute.

Think of it as a different product that happens to share a repository.
If you're writing a source (docker image that runs task handlers), use
`ogpu.service`. If you're writing a client or a scheduler, use the rest
of the SDK.

This page is a short API overview. For end-to-end source development
(docker compose structure, pytorch/tensorflow integration, model
downloading, etc.), see the OpenGPU protocol documentation.

!!! info "Frozen in v0.2.1"
    The `ogpu.service` module was not refactored as part of the v0.2.1
    SDK release. It's the framework source developers use inside their
    docker containers, and its stability is important for deployed
    sources. Any cleanup is deferred to a future release.

---



## Decorators

::: ogpu.service.decorators.expose
    options:
      show_root_heading: true
      heading_level: 3

::: ogpu.service.decorators.init
    options:
      show_root_heading: true
      heading_level: 3

## Starting the service

::: ogpu.service.server.start
    options:
      show_root_heading: true
      heading_level: 3

## Minimal example

```python
import ogpu.service
from pydantic import BaseModel

class Input(BaseModel):
    text: str

class Output(BaseModel):
    result: str
    confidence: float

@ogpu.service.init()
def setup():
    ogpu.service.logger.info("Loading model...")

@ogpu.service.expose()
def predict(data: Input) -> Output:
    return Output(result="positive", confidence=0.97)

ogpu.service.start()
```

- `@init()` runs once on startup — load models, download files, etc.
- `@expose()` marks a function as network-callable. The name becomes
  the task's `function_name`.
- Input/output must be Pydantic models.
- `ogpu.service.start()` launches the FastAPI server that providers
  call when a task is dispatched to your source.

!!! info "Frozen in v0.2.1"
    The `ogpu.service` module was not refactored in the v0.2.1 release.
    It is the framework source developers use inside their docker
    containers to expose handler functions, and its stability is
    important for deployed sources. Any cleanup is deferred to a
    future release.
