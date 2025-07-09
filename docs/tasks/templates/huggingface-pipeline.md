# HuggingFace Pipeline Tasks

Learn how to publish tasks for HuggingFace Pipeline sources. This guide provides the exact function name, input structure, and examples for working with HuggingFace Ready environments.

## 🎯 Function Interface

HuggingFace Pipeline sources use a standardized interface:

- **Function Name**: `inference`
- **Input Model**: `Inference` with `input` and `args` fields

```python
class Inference(BaseModel):
    input: str | dict    # Your input data (text, image, etc.)
    args: dict = {}      # Additional pipeline arguments
```

## 🚀 Quick Task Publishing

### Basic Text Classification Task

```python
import ogpu.client
import time
from web3 import Web3

# Configure chain
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)

# Publish task to HuggingFace Pipeline source
task_info = ogpu.client.TaskInfo(
    source="your_hf_source_address_here",
    config=ogpu.client.TaskInput(
        function_name="inference",
        data={
            "input": "This movie is absolutely fantastic!",
            "args": {}
        }
    ),
    expiryTime=int(time.time()) + 600,     # 10 minutes
    payment=Web3.to_wei(0.002, "ether")   # 0.002 OGPU
)

task_address = ogpu.client.publish_task(task_info)
print(f"✅ Task published: {task_address}")
```

## 📊 Input Examples by Task Type

### 📝 Text Classification

```python
data = {
    "input": "I love this product! It's amazing.",
    "args": {}
}
```

### 🖼️ Image Classification

```python
data = {
    "input": "https://example.com/image.jpg",  # Image URL or base64
    "args": {}
}
```

### 💬 Text Generation

```python
data = {
    "input": "Once upon a time",
    "args": {
        "max_length": 100,
        "temperature": 0.7,
        "num_return_sequences": 1
    }
}
```

### 🔀 Visual Question Answering

```python
data = {
    "input": {
        "question": "What is in this image?",
        "image": "https://example.com/image.jpg"
    },
    "args": {}
}
```

### 🌐 Translation

```python
data = {
    "input": "Hello, how are you?",
    "args": {
        "src_lang": "en",
        "tgt_lang": "fr"
    }
}
```

### 📄 Summarization

```python
data = {
    "input": "Long article text here...",
    "args": {
        "max_length": 150,
        "min_length": 50
    }
}
```

## 🔧 Advanced Task Configuration

### Multiple Text Inputs

```python
data = {
    "input": [
        "First text to classify",
        "Second text to classify", 
        "Third text to classify"
    ],
    "args": {}
}
```

### Custom Pipeline Arguments

```python
data = {
    "input": "Generate creative text",
    "args": {
        "max_length": 200,
        "temperature": 0.8,
        "top_p": 0.9,
        "do_sample": True,
        "num_return_sequences": 3
    }
}
```

### Image with Custom Parameters

```python
data = {
    "input": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "args": {
        "top_k": 5,
        "confidence_threshold": 0.8
    }
}
```


## 🎯 Complete Task Examples

### Sentiment Analysis Task

```python
import ogpu.client
import time
from web3 import Web3

ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)

task_info = ogpu.client.TaskInfo(
    source="0x1234567890123456789012345678901234567890",  # Your HF source
    config=ogpu.client.TaskInput(
        function_name="inference",
        data={
            "input": "The customer service was excellent and very helpful!",
            "args": {}
        }
    ),
    expiryTime=int(time.time()) + 300,
    payment=Web3.to_wei(0.001, "ether")
)

task_address = ogpu.client.publish_task(task_info)
```

### Image Classification Task

```python
task_info = ogpu.client.TaskInfo(
    source="0x1234567890123456789012345678901234567890",
    config=ogpu.client.TaskInput(
        function_name="inference",
        data={
            "input": "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png",
            "args": {
                "top_k": 3
            }
        }
    ),
    expiryTime=int(time.time()) + 400,
    payment=Web3.to_wei(0.002, "ether")
)

task_address = ogpu.client.publish_task(task_info)
```

### Text Generation with Custom Args

```python
task_info = ogpu.client.TaskInfo(
    source="0x1234567890123456789012345678901234567890",
    config=ogpu.client.TaskInput(
        function_name="inference",
        data={
            "input": "Write a short story about artificial intelligence:",
            "args": {
                "max_length": 200,
                "temperature": 0.8,
                "top_p": 0.9,
                "num_return_sequences": 2
            }
        }
    ),
    expiryTime=int(time.time()) + 600,
    payment=Web3.to_wei(0.004, "ether")
)

task_address = ogpu.client.publish_task(task_info)
```

## 🔍 Task Response Handling

### Expected Response Format

HuggingFace Pipeline tasks return responses in this format:

```python
# Text classification response
{
    "result": [
        {"label": "POSITIVE", "score": 0.9998}
    ]
}

# Text generation response  
{
    "result": [
        {"generated_text": "Once upon a time, there was a brave knight..."}
    ]
}

# Image classification response
{
    "result": [
        {"label": "Egyptian cat", "score": 0.9421},
        {"label": "tabby, tabby cat", "score": 0.0876}
    ]
}
```

### Processing Task Results

```python
import ogpu.client

# Get task responses
responses = ogpu.client.get_responses(task_address)

for response in responses:
    if response.confirmed:
        result = response.data
        print(f"Task result: {result}")
        
        # Process based on task type
        if "generated_text" in str(result):
            # Text generation result
            generated = result["result"][0]["generated_text"]
            print(f"Generated: {generated}")
        elif "label" in str(result):
            # Classification result
            prediction = result["result"][0]
            print(f"Prediction: {prediction['label']} ({prediction['score']:.4f})")
```

---

Ready to publish HuggingFace tasks! 🚀
