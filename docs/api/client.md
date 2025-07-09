# API Reference: ogpu.client

Essential API reference for the `ogpu.client` module - the foundation for **task publishing and response management** on the OpenGPU network.

!!! info "Task and Source Management"
    **This module is designed for interacting with the OpenGPU network.** Use `ogpu.client` to publish tasks, manage sources, retrieve responses, and configure blockchain connections.

## Source Operations

::: ogpu.client.source.publish_source
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false


**Purpose:** Publish AI services as sources on the OpenGPU network.

**Example:**
```python
from web3 import Web3
from ogpu.client import publish_source, SourceInfo, ImageEnvironments, DeliveryMethod

source_info = SourceInfo(
    name="sentiment-service",
    description="AI sentiment analysis service",
    logoUrl="https://example.com/logo.png",
    imageEnvs=ImageEnvironments(
        cpu="https://raw.githubusercontent.com/user/repo/main/docker-compose.yml",
        nvidia="https://raw.githubusercontent.com/user/repo/main/docker-compose-gpu.yml"
    ),
    minPayment=Web3.to_wei(0.001, "ether"),
    minAvailableLockup=Web3.to_wei(0.01, "ether"),
    maxExpiryDuration=86400,
    deliveryMethod=DeliveryMethod.MANUAL_CONFIRMATION
)

source_address = publish_source(source_info)
print(f"Source published at: {source_address}")
```

---

## Task Operations


::: ogpu.client.task.publish_task
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Publish AI tasks to the OpenGPU network for distributed processing.

**Example:**
```python
import time
from web3 import Web3
from ogpu.client import publish_task, TaskInfo, TaskInput

# Create task configuration
task_config = TaskInput(
    function_name="analyze_sentiment",
    data={"text": "I love this product!"}
)

task_info = TaskInfo(
    source="0x1234567890123456789012345678901234567890",
    config=task_config,
    expiryTime=int(time.time()) + 3600,  # 1 hour from now
    payment=Web3.to_wei(0.01, "ether")
)

task_address = publish_task(task_info)
print(f"Task published at: {task_address}")
```

---


## Response Operations


::: ogpu.client.responses.get_task_responses
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Retrieve all responses for a published task.

**Example:**
```python
responses = get_task_responses(task_address)
for response in responses:
    print(f"Provider: {response.provider}")
    print(f"Status: {response.status}")
    print(f"Data: {response.data}")
```

---

::: ogpu.client.responses.get_confirmed_response
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Retrieve the confirmed response for a completed task.

**Example:**
```python
confirmed = get_confirmed_response(task_address)
if confirmed:
    print(f"Result: {confirmed.data}")
```

---

::: ogpu.client.responses.confirm_response
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Confirm a response to complete the task and release payment.

**Example:**
```python
tx_hash = confirm_response(response_address)
print(f"Confirmation transaction: {tx_hash}")
```

---


## Network Configuration

::: ogpu.client.chain_config.ChainId
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Enum defining supported blockchain networks.

---

::: ogpu.client.chain_config.ChainConfig.set_chain
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Set the current active blockchain network.

**Example:**
```python
from ogpu.client import ChainConfig, ChainId

# Set to testnet
ChainConfig.set_chain(ChainId.OGPU_TESTNET)

# Set to mainnet
ChainConfig.set_chain(ChainId.OGPU_MAINNET)
```

---

::: ogpu.client.chain_config.ChainConfig.get_current_chain
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Get the currently active blockchain network.

**Example:**
```python
current_chain = ChainConfig.get_current_chain()
print(f"Current chain: {current_chain.name}")
print(f"Chain ID: {current_chain.value}")
```

---

::: ogpu.client.chain_config.ChainConfig.get_contract_address
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Get contract address for a specific contract on the current chain.

**Example:**
```python
# Get contract addresses for current chain
nexus_address = ChainConfig.get_contract_address("NEXUS")
controller_address = ChainConfig.get_contract_address("CONTROLLER")
terminal_address = ChainConfig.get_contract_address("TERMINAL")

print(f"NEXUS: {nexus_address}")
print(f"CONTROLLER: {controller_address}")
print(f"TERMINAL: {terminal_address}")
```

---

::: ogpu.client.chain_config.ChainConfig.get_all_supported_chains
    options:
      show_source: true
      heading_level: 3
      show_root_heading: true
      show_signature: false

**Purpose:** Get list of all supported blockchain networks.

**Example:**
```python
supported_chains = ChainConfig.get_all_supported_chains()
for chain in supported_chains:
    print(f"Chain: {chain.name} (ID: {chain.value})")
```

---


## Data Types

::: ogpu.client.types.ImageEnvironments
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Docker compose file URLs for different hardware environments.

**Example:**
```python
image_envs = ImageEnvironments(
    cpu="https://raw.githubusercontent.com/user/repo/main/docker-compose.yml",
    nvidia="https://raw.githubusercontent.com/user/repo/main/docker-compose-gpu.yml",
    amd="https://raw.githubusercontent.com/user/repo/main/docker-compose-amd.yml"
)
```

---

::: ogpu.client.types.DeliveryMethod
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Enum defining how task responses are delivered and confirmed.

---

::: ogpu.client.types.SourceInfo
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Configuration data for publishing AI services as sources.

**Example:**
```python
source_info = SourceInfo(
    name="sentiment-service",
    description="AI sentiment analysis service",
    logoUrl="https://example.com/logo.png",
    imageEnvs=ImageEnvironments(
        cpu="https://raw.githubusercontent.com/user/repo/main/docker-compose.yml",
        nvidia="https://raw.githubusercontent.com/user/repo/main/docker-compose-gpu.yml"
    ),
    minPayment=Web3.to_wei(0.001, "ether"),
    minAvailableLockup=Web3.to_wei(0.01, "ether"),
    maxExpiryDuration=86400,
    deliveryMethod=DeliveryMethod.MANUAL_CONFIRMATION
)
```

---

::: ogpu.client.types.TaskInput
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Configuration for task input data and function specification.

**Example:**
```python
# Using a dictionary
task_input = TaskInput(
    function_name="inference",
    data={"inputs": "Translate to French: Hello"}
)

# Using a Pydantic model
from pydantic import BaseModel

class InferenceData(BaseModel):
    inputs: str
    parameters: dict = {}

task_input = TaskInput(
    function_name="inference", 
    data=InferenceData(inputs="Hello world")
)
```

---

::: ogpu.client.types.TaskInfo
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Configuration data for publishing tasks to the network.

**Example:**
```python
task_info = TaskInfo(
    source="0x1234...",
    config=TaskInput(
        function_name="inference",
        data={"inputs": "What is AI?"}
    ),
    expiryTime=1640995200,
    payment=1000000000000000000  # 1 OGPU in wei
)
```

---

::: ogpu.client.types.Response
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Response data structure from completed tasks.

**Example:**
```python
# Response object from get_task_responses()
response = Response(
    address="0xabcd...",
    task="0x1234...",
    provider="0x5678...",
    data='{"result": "positive sentiment"}',
    payment=1000000000000000000,
    status=1,
    timestamp=1640995200,
    confirmed=False
)
```

---

::: ogpu.client.types.ConfirmedResponse
    options:
        members: []
        show_source: false
        heading_level: 3
        show_root_heading: true
        show_docstring_attributes: true
        show_signature: false

**Purpose:** Simplified confirmed response data structure.

**Example:**
```python
# Confirmed response from get_confirmed_response()
confirmed = ConfirmedResponse(
    address="0xabcd...",
    data='{"result": "positive sentiment", "confidence": 0.95}'
)
```
