# Publishing Tasks

Learn how to create,     },
    expiryTime=int(time.time()) + 3600,  # 1 hour from now
    payment=Web3.to_wei(0.01, "ether")   # 0.01 OGPU
)igure, and publish computational tasks on the OpenGPU network.

!!! info "Configuration Details"
    For detailed parameter configuration and examples, see [Task Configuration](configuration.md).

## 🎯 Overview

Publishing a task involves:
1. **Configuring** task parameters and input data
2. **Setting** payment and expiry details  
3. **Publishing** to the blockchain
4. **Monitoring** for responses

## 🛠️ Basic Task Publishing

### Step 1: Import Required Libraries

```python
import ogpu.client
import time
from web3 import Web3

# Configure for testnet
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)
```

### Step 2: Create Task Configuration

```python
# Define your task
task_info = ogpu.client.TaskInfo(
    source="0x1234567890abcdef...",  # Your source address
    config=ogpu.client.TaskInput(
        function_name="text2text",
        data={
            "messages": [
                {"role": "user", "content": "Write a haiku about AI"}
            ]
        }
    ),
    expiryTime=int(time.time()) + 3600,  # 1 hour from now
    payment=Web3.to_wei(0.01, "ether")   # 0.01 OGPU
)
```

### Step 3: Publish the Task

```python
try:
    task_address = ogpu.client.publish_task(task_info)
    print(f"✅ Task published successfully!")
    print(f"📍 Task address: {task_address}")
    print(f"🔗 Explorer: https://ogpuscan.io/task/{task_address}")
except Exception as e:
    print(f"❌ Failed to publish task: {e}")
```

## 📊 Complete Example: Text Generation

```python
#!/usr/bin/env python3
"""
Example: Publishing a text generation task
"""
import ogpu.client
import time
from web3 import Web3

def main():
    # Configure chain
    ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)
    
    # Create text generation task
    task_info = ogpu.client.TaskInfo(
        source="0x1234567890abcdef...",  # Replace with your source
        config=ogpu.client.TaskInput(
            function_name="text2text",
            data={
                "messages": [
                    {
                        "role": "user", 
                        "content": "Explain quantum computing in simple terms"
                    }
                ]
            }
        ),
        expiryTime=int(time.time()) + 3600,  # 1 hour
        payment=Web3.to_wei(0.01, "ether")   # 0.01 OGPU
    )
    
    try:
        # Publish task
        print("🚀 Publishing task...")
        task_address = ogpu.client.publish_task(task_info)
        
        print(f"✅ Task published successfully!")
        print(f"📍 Address: {task_address}")
        print(f"💰 Payment: 0.01 OGPU")
        print(f"⏰ Expires: {time.ctime(task_info.expiryTime)}")
        
        return task_address
        
    except Exception as e:
        print(f"❌ Failed to publish task: {e}")
        return None

if __name__ == "__main__":
    task_address = main()
```

## 🔧 Advanced Configuration

### Multi-Message Conversations

```python
# Complex conversation task
task_config = ogpu.client.TaskInput(
    function_name="text2text",
    data={
        "messages": [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is..."},
            {"role": "user", "content": "Can you give me an example?"}
        ]
    }
)
```

### Custom Function Parameters

```python
# Task with custom parameters
task_config = ogpu.client.TaskInput(
    function_name="process_data",
    data={
        "text": "Process this text",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 500,
            "format": "json"
        }
    }
)
```

### Payment Strategies

```python
# Different payment amounts
payment_low = Web3.to_wei(0.001, "ether")    # 0.001 OGPU - basic tasks
payment_medium = Web3.to_wei(0.01, "ether")  # 0.01 OGPU - standard tasks  
payment_high = Web3.to_wei(0.1, "ether")     # 0.1 OGPU - complex tasks

# Expiry timing
expiry_short = int(time.time()) + 300      # 5 minutes
expiry_medium = int(time.time()) + 3600    # 1 hour
expiry_long = int(time.time()) + 86400     # 24 hours
```

## 🎛️ Task Management

### Check Task Status

```python
def check_task_status(task_address: str):
    """Check if task has been completed"""
    try:
        responses = ogpu.client.get_task_responses(task_address)
        
        if not responses:
            print("⏳ No responses yet")
            return False
            
        for response in responses:
            if response.confirmed:
                print(f"✅ Task completed!")
                print(f"📝 Result: {response.data}")
                return True
        
        print(f"📨 {len(responses)} responses received, awaiting confirmation")
        return False
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False
```

### Monitor Task Progress

```python
import time

def monitor_task(task_address: str, timeout: int = 3600):
    """Monitor task until completion or timeout"""
    start_time = time.time()
    
    print(f"🔍 Monitoring task: {task_address}")
    
    while time.time() - start_time < timeout:
        if check_task_status(task_address):
            return True
            
        print("⏳ Waiting for responses...")
        time.sleep(30)  # Check every 30 seconds
    
    print("⏰ Task monitoring timed out")
    return False

# Usage
task_address = publish_task(task_info)
if task_address:
    monitor_task(task_address)
```

## 🚨 Error Handling

### Common Issues

```python
def robust_task_publishing(task_info):
    """Publish task with comprehensive error handling"""
    try:
        # Validate task configuration
        if not task_info.source:
            raise ValueError("Source address is required")
            
        if task_info.payment <= 0:
            raise ValueError("Payment must be greater than 0")
            
        if task_info.expiryTime <= int(time.time()):
            raise ValueError("Expiry time must be in the future")
        
        # Publish task
        task_address = ogpu.client.publish_task(task_info)
        return task_address
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Publishing failed: {e}")
        return None
```

### Retry Logic

```python
import time
from typing import Optional

def publish_with_retry(task_info, max_retries: int = 3) -> Optional[str]:
    """Publish task with retry logic"""
    for attempt in range(max_retries):
        try:
            task_address = ogpu.client.publish_task(task_info)
            print(f"✅ Task published on attempt {attempt + 1}")
            return task_address
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("❌ All retry attempts failed")
                
    return None
```

## 💡 Best Practices

### 1. Task Validation

```python
def validate_task_config(task_info):
    """Validate task configuration before publishing"""
    checks = [
        (task_info.source, "Source address is required"),
        (task_info.config.function_name, "Function name is required"),
        (task_info.config.data, "Input data is required"),
        (task_info.payment > 0, "Payment must be positive"),
        (task_info.expiryTime > int(time.time()), "Expiry must be future")
    ]
    
    for check, message in checks:
        if not check:
            raise ValueError(message)
    
    print("✅ Task configuration valid")
```

### 2. Payment Estimation

```python
def estimate_payment(complexity: str) -> int:
    """Estimate appropriate payment based on task complexity"""
    rates = {
        "simple": Web3.to_wei(0.001, "ether"),   # Basic text processing
        "medium": Web3.to_wei(0.01, "ether"),    # AI inference
        "complex": Web3.to_wei(0.1, "ether"),    # Heavy computation
    }
    
    return rates.get(complexity, rates["medium"])

# Usage
payment = estimate_payment("medium")
```

### 3. Batch Task Publishing

```python
def publish_batch_tasks(tasks: list) -> list:
    """Publish multiple tasks efficiently"""
    task_addresses = []
    
    for i, task_info in enumerate(tasks):
        print(f"📤 Publishing task {i+1}/{len(tasks)}")
        
        try:
            address = ogpu.client.publish_task(task_info)
            task_addresses.append(address)
            print(f"✅ Task {i+1} published: {address}")
            
        except Exception as e:
            print(f"❌ Task {i+1} failed: {e}")
            task_addresses.append(None)
        
        # Small delay to avoid rate limits
        time.sleep(1)
    
    return task_addresses
```

## 🎯 Next Steps

- **[Task Configuration](configuration.md)** - Detailed parameter configuration  
- **[Responses Overview](../responses/index.md)** - Handle task results
- **[Sources Overview](../sources/index.md)** - Create your own sources

Ready to publish your first task! 🚀
