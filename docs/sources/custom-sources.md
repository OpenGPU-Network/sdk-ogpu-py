# Custom Sources

Learn how to build and deploy your own custom services using the OpenGPU SDK. This guide covers the complete workflow from writing custom code to deploying on the network.

!!! info "Complete Control"
    Custom sources give you full control over your service implementation. You write your own code using our SDK, containerize it with Docker, and deploy it on the OpenGPU network. Perfect for specialized algorithms, proprietary models, or complex business logic.

## 🎯 When to Use Custom Sources

Choose custom sources when you need:

- **Custom algorithms** and specialized processing logic
- **Proprietary models** or business-specific implementations  
- **Complex workflows** with multiple steps or services
- **Specific dependencies** not available in pre-built environments
- **Full control** over the execution environment
- **Advanced optimizations** for your specific use case


## 🛠️ Step 1: Write Your Service Code

Create your custom service using the OpenGPU SDK:


### Ollama Service

First, create the data models:

```python
# models.py
from typing import List
from pydantic import BaseModel

class Message(BaseModel):
    role: str = "user"
    content: str = "what is the capital of France?"

class InputData(BaseModel):
    messages: List[Message]
```

Then, create the main service:

```python
# ollama_service.py
import ollama
from ollama import chat
from ollama import ChatResponse
import ogpu.service
from models import InputData, Message

MODEL_NAME = "qwen2.5:3b"

@ogpu.service.init()
def setup():
    """Initialize Ollama and pull the model"""
    ogpu.service.logger.info(f"Pulling {MODEL_NAME} model...")
    ollama.pull(MODEL_NAME)
    ogpu.service.logger.info(f"{MODEL_NAME} pulled.")

@ogpu.service.expose()
def text2text(input_data: InputData) -> Message:
    """Generate text response using Ollama chat interface"""
    ogpu.service.logger.info(f"Generating Text2Text response..")
    
    try:
        # Use Ollama's chat interface for conversation
        response: ChatResponse = chat(model=MODEL_NAME, messages=[
            {"role": msg.role, "content": msg.content} 
            for msg in input_data.messages
        ])
        
        output = Message(
            role=response['message']['role'],
            content=response['message']['content']
        )
        
        ogpu.service.logger.info(f"Task completed.")
        return output
        
    except Exception as e:
        ogpu.service.logger.error(f"An error occurred: {e}")
        raise e


if __name__ == "__main__":
    ogpu.service.start()
```


---


## 🐳 Step 2: Create Dockerfile

Create a Dockerfile to containerize your service:

### Basic Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5555

# Command to run the application
CMD ["python", "main.py"]
```


### Requirements File

```txt
# requirements.txt
ogpu
ollama>=0.4.0
```

---

## 🔨 Step 3: Build Docker Image

### Build Your Images

```bash
# Build image
docker build -t opengpunetwork/openchat-text2text:latest .

# Check images
docker images | grep openchat-text2text
```

---

## 📦 Step 4: Push to Docker Registry

### Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push image
docker push opengpunetwork/openchat-text2text:latest
```

---

## 🐳 Step 5: Create Docker Compose Files

Create Docker Compose configurations for your Ollama service:

### GPU-Enabled Ollama Compose

```yaml
# docker-compose-ollama.yml
services:

  openchat-ollama-service:
    image: ollama/ollama:latest
    ports:
      - "12436:11434"
    pull_policy: always
    volumes:
      - ollama_models:/root/.ollama
    networks:
      - app_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  openchat-t2t-service:
    image: opengpunetwork/openchat-text2text:latest@sha256:daf5714a1f8f2b9031d9ed62ffb4cd3763e5ff2bf1063cb58f7b5d90362e4c5e
    pull_policy: always
    ports:
      - "${PORT}:5555"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - CALLBACK_URL=${CALLBACK_URL}
      - OLLAMA_HOST=http://host.docker.internal:12436
    depends_on:
      - openchat-ollama-service
    networks:
      - app_network

networks:
  app_network:
    driver: bridge

volumes:
  ollama_models:
    driver: local
```


### Test Compose Files Locally

```bash
# Test Ollama compose
docker-compose -f docker-compose-ollama.yml up -d

# Check logs
docker-compose -f docker-compose-ollama.yml logs -f

# Stop
docker-compose -f docker-compose-ollama.yml down
```

---

## 🌐 Step 6: Host Your Compose Files

Make your Docker Compose files publicly accessible:

- GitHub


- IPFS


- Web Server

---

## 📋 Step 7: Publish Your Source

Create and publish your custom source:

```python
# publish_custom_source.py
import ogpu.client
from web3 import Web3

# publish_ollama_source.py
import ogpu.client
from web3 import Web3

# Configure chain
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)

# Create Ollama-powered chat service
source_info = SourceInfo(
    name="OpenChat - text2text",
    description="The AI model that powers the text2text functionality of the OpenChat bot.",
    logoUrl="https://raw.githubusercontent.com/OpenGPU-Network/assets/main/ogpu-logo.png",
    imageEnvs= ImageEnvironments(
        cpu="https://raw.githubusercontent.com/OpenGPU-Network/openchat-text2text/refs/heads/main/docker-compose/cpu.yml",
        nvidia="https://raw.githubusercontent.com/OpenGPU-Network/openchat-text2text/refs/heads/main/docker-compose/nvidia.yml",
        amd="https://raw.githubusercontent.com/OpenGPU-Network/openchat-text2text/refs/heads/main/docker-compose/amd.yml"
    ),
    minPayment=Web3.to_wei(0.001, "ether"),
    minAvailableLockup=Web3.to_wei(0, "ether"),
    maxExpiryDuration=86400,  # 24 hour in seconds
    deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
)

source_address = publish_source(source_info)
print(f"Source published successfully at: {source_address}")
```

---


### Debugging Tips

1. **Local Testing First**
   - Always test your service locally before containerizing
   - Use `python ollama_service.py` and test with the Swagger UI at `/docs`

2. **Step-by-Step Verification**
   - Test Docker image locally before pushing
   - Verify compose files work locally
   - Check public accessibility of compose files

3. **Monitor Logs**
   - Add comprehensive logging to your service
   - Monitor Docker container logs after deployment

---

## 🎯 Next Steps

- **[Configuration](configuration.md)** - Advanced source configuration options
- **[Publishing Tasks](../tasks/publishing-tasks.md)** - How to use your custom sources

Ready to build amazing custom services! 💪