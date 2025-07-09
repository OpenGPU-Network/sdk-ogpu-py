# Task Configuration

Learn how to configure and publish computational tasks on the OpenGPU network. This guide covers task parameters, input data structures, and publishing options.

## 📋 Prerequisites

Before configuring any task, ensure you have:

- ✅ **OpenGPU SDK installed** ([Installation Guide](../getting-started/installation.md))
- ✅ **Wallet configured** with private key in environment variables
- ✅ **Chain configuration** set up (testnet or mainnet)
- ✅ **Published source** available on the network
- ✅ **Sufficient OGPU** for gas fees in your wallet

### Environment Setup

```bash
# Set your private key
export CLIENT_PRIVATE_KEY="your_private_key_here"

# Verify installation
python -c "import ogpu.client; print('OpenGPU SDK ready!')"
```

---

## 🔧 TaskInfo Configuration

All tasks use the same `TaskInfo` structure:

```python
import ogpu.client
from web3 import Web3

task_info = ogpu.client.TaskInfo(
    source="0x4F1477E0a1DA8340E964D01e32Dff302F3CB203A",  # Published source address
    config=ogpu.client.TaskInput(                          # Input configuration
        function_name="text2text",                         # Function to call
        data={                                             # Input data
            "messages": [
                {"role": "user", "content": "Hello world!"}
            ]
        }
    ),
    expiryTime=int(time.time()) + 3600,                   # Expiry timestamp
    payment=Web3.to_wei(0.01, "ether")                    # Payment amount
)
```

## 📊 Configuration Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `source` | `str` | Address of published source | `"0x4F1477E0a1DA8340E964D01e32Dff302F3CB203A"` |
| `config` | `TaskInput` | Function and data configuration | See examples below |
| `expiryTime` | `int` | Task expiry timestamp (Unix) | `int(time.time()) + 3600` |
| `payment` | `int` | Payment amount in wei | `Web3.to_wei(0.01, "ether")` |

---

## 🎯 Function Name & Data Mapping

### Connection to Custom Services

The `function_name` and `data` must match your published source:

```python
# In your custom service (e.g., ollama_service.py)
@ogpu.service.expose()
def text2text(input_data: InputData) -> Message:  # ← function_name = "text2text"
    # Your service logic here
    pass

# Your service's input model (e.g., models.py)
class InputData(BaseModel):                       # ← This defines data structure
    messages: List[Message]

class Message(BaseModel):
    role: str
    content: str
```

### Task Configuration Mapping

```python
config = ogpu.client.TaskInput(
    function_name="text2text",    # ← Matches your exposed function name
    data={                        # ← Must match InputData structure
        "messages": [             #   ↓ Matches InputData.messages
            {
                "role": "user",   #   ↓ Matches Message.role
                "content": "Hi!"  #   ↓ Matches Message.content
            }
        ]
    }
)
```

!!! info "Validation Tip"
    Test your function_name and data structure locally before publishing tasks:
    ```bash
    python your_service.py
    # Visit http://localhost:5555/docs to test the API
    ```

---

## 💰 Payment Configuration

Configure task payment using Wei conversion:

### Basic Payment Setup

```python
# Common payment amounts
payment = Web3.to_wei(0.001, "ether")    # 0.001 OGPU (small tasks)
payment = Web3.to_wei(0.01, "ether")     # 0.01 OGPU (medium tasks)  
payment = Web3.to_wei(0.1, "ether")      # 0.1 OGPU (large tasks)

# Alternative units
payment = Web3.to_wei(10, "gwei")        # 10 Gwei
payment = 1000000000000000000             # 1 OGPU in wei (direct)
```

### Payment Guidelines

| Task Type | Suggested Payment | Description |
|-----------|------------------|-------------|
| Simple text | 0.001-0.005 OGPU | Basic Q&A, simple processing |
| AI inference | 0.005-0.02 OGPU | LLM responses, image analysis |
| Complex compute | 0.02-0.1 OGPU | Heavy processing, long tasks |

---

## ⏰ Expiry Time Configuration

Set appropriate task timeouts:

### Time Configuration Examples

```python
import time

# Short tasks (5 minutes)
expiryTime = int(time.time()) + 300

# Medium tasks (30 minutes)  
expiryTime = int(time.time()) + 1800

# Long tasks (2 hours)
expiryTime = int(time.time()) + 7200

# Dynamic timeout based on complexity
def calculate_timeout(task_complexity: str) -> int:
    timeouts = {
        "simple": 300,      # 5 minutes
        "medium": 1800,     # 30 minutes  
        "complex": 7200     # 2 hours
    }
    return int(time.time()) + timeouts.get(task_complexity, 1800)
```

### Timeout Guidelines

- **Simple tasks**: 5-15 minutes
- **AI inference**: 15-30 minutes
- **Heavy compute**: 30 minutes - 2 hours
- **Consider provider startup time**: Add 2-5 minutes buffer

---

## 🚀 Publishing Your Task

Configure and publish your task to the OpenGPU network:

### Chain Configuration

```python
# Configure chain (testnet for development)
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)

# For mainnet deployment
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_MAINNET)
```

### Publication Process

```python
try:
    task_address = ogpu.client.publish_task(task_info)
    print(f"✅ Task published successfully!")
    print(f"Task address: {task_address}")
except Exception as e:
    print(f"❌ Failed to publish task: {e}")
```

### Private Key Configuration

The SDK automatically uses your private key from environment variables:

```bash
export CLIENT_PRIVATE_KEY="your_private_key_here"
```

Or pass it explicitly:

```python
task_address = ogpu.client.publish_task(
    task_info=task_info,
    private_key="your_private_key_here"
)
```

---

## 🔧 Validation Checklist

- ✅ Source address is valid and deployed
- ✅ Function name matches your service's exposed function
- ✅ Data structure matches your service's input model
- ✅ Private key is configured correctly
- ✅ Wallet has sufficient $OGPU for gas
- ✅ Chain configuration matches your target network
- ✅ Payment amount is reasonable for task complexity
- ✅ Timeout duration allows sufficient execution time

---

## 🎯 Configuration Examples

### Simple Text Processing

```python
# Basic text processing task
simple_task = ogpu.client.TaskInfo(
    source="0x4F1477E0a1DA8340E964D01e32Dff302F3CB203A",
    config=ogpu.client.TaskInput(
        function_name="text2text",
        data={
            "messages": [
                {"role": "user", "content": "What is AI?"}
            ]
        }
    ),
    expiryTime=int(time.time()) + 600,    # 10 minutes
    payment=Web3.to_wei(0.005, "ether")   # 0.005 OGPU
)
```

### Complex AI Task

```python
# Complex AI processing task
complex_task = ogpu.client.TaskInfo(
    source="0x4F1477E0a1DA8340E964D01e32Dff302F3CB203A",
    config=ogpu.client.TaskInput(
        function_name="analyze_document",
        data={
            "document": "Long document content here...",
            "analysis_type": "comprehensive",
            "include_summary": True,
            "max_length": 500
        }
    ),
    expiryTime=int(time.time()) + 3600,   # 1 hour
    payment=Web3.to_wei(0.02, "ether")    # 0.02 OGPU
)
```

### Batch Processing Task

```python
# Batch processing multiple items
batch_task = ogpu.client.TaskInfo(
    source="0x4F1477E0a1DA8340E964D01e32Dff302F3CB203A",
    config=ogpu.client.TaskInput(
        function_name="process_batch",
        data={
            "items": [
                {"text": "Process this first"},
                {"text": "Process this second"},
                {"text": "Process this third"}
            ],
            "batch_size": 3
        }
    ),
    expiryTime=int(time.time()) + 1800,   # 30 minutes
    payment=Web3.to_wei(0.015, "ether")   # 0.015 OGPU
)
```

---

## 💡 Practical Example: Using Your Custom Ollama Service

Complete example using the Ollama service from [Custom Sources](../sources/custom-sources.md):

```python
import ogpu.client
import time
from web3 import Web3

# Configure testnet
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)

def create_ollama_task(question: str, payment_ogpu: float = 0.0035):
    """Create a task for your Ollama service"""
    
    task_info = ogpu.client.TaskInfo(
        source="0x4F1477E0a1DA8340E964D01e32Dff302F3CB203A",  # Your Ollama source
        config=ogpu.client.TaskInput(
            function_name="text2text",                          # Exposed function
            data={                                              # Matches InputData
                "messages": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            }
        ),
        expiryTime=int(time.time()) + 600,   # 10 minutes
        payment=Web3.to_wei(payment_ogpu, "ether")
    )
    
    # Publish the task
    task_address = ogpu.client.publish_task(task_info)
    print(f"🚀 Task published: {task_address}")
    
    return task_address

# Usage examples
task1 = create_ollama_task("Explain quantum computing simply")
task2 = create_ollama_task("Write a Python function to sort lists", 0.01)
task3 = create_ollama_task("Summarize the benefits of renewable energy")
```

---

## 🎯 Next Steps

### After Configuration:
- **[Publishing Tasks](publishing-tasks.md)** - Complete publishing workflow
- **[Responses Overview](../responses/index.md)** - Handle task results

### Advanced Topics:
- **[Sources Overview](../sources/index.md)** - Create custom task environments
- **[API Reference](../api/client.md)** - Complete API documentation

---

## 🆘 Need Help?

- **[GitHub Examples](https://github.com/OpenGPU-Network/sdk-ogpu-py/tree/main/examples)** - Reference implementations
- **[Issues](https://github.com/OpenGPU-Network/sdk-ogpu-py/issues)** - Report problems or ask questions
- **[Documentation](../index.md)** - Browse all guides

Ready to configure your tasks! 🚀
