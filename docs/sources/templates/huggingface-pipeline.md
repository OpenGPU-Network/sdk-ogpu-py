# Hugging Face Ready Environment

The Hugging Face Ready environment provides a pre-configured service for running Hugging Face models without writing any code. Simply configure your model parameters and publish your source!

!!! warning "Pipeline Task Limitation"
    **Important**: Hugging Face Ready only supports **high-level pipeline tasks** from the Transformers library. Your parameters (`task` and `model`) are passed directly to the Hugging Face `pipeline()` function. You cannot run arbitrary custom code - only the predefined pipeline tasks like text-classification, image-classification, text-generation, etc.

!!! info "Configuration Method"
    **Key Point**: Model configuration must be done in the Docker Compose file using the `PIPE_ARGS_STR` environment variable. The metadata approach is not effective. You must create and host your own Docker Compose files with your specific model configuration.

## 🎯 Overview

The Hugging Face Ready environment (`opengpunetwork/hfr-client`) comes with:

- ✅ **Pre-installed Hugging Face libraries** (transformers, datasets, etc.)
- ✅ **GPU acceleration support** (NVIDIA CUDA)
- ✅ **Automatic model loading** from Hugging Face Hub
- ✅ **Caching system** for faster model loading
- ✅ **Ready-to-use service** - no coding required!
- ⚠️ **Pipeline tasks only** - uses Hugging Face `pipeline()` directly

## 🚀 Quick Start

### Step 1: Choose Your Model and Task

Browse [Hugging Face Hub](https://huggingface.co/models) and select your model. Note the:

- **Task type** (e.g., "visual-question-answering", "text-classification", "image-classification")
- **Model name** (e.g., "dandelin/vilt-b32-finetuned-vqa")

### Step 2: Create Your Docker Compose Configuration

Create a Docker Compose file with your model configuration:

```yaml
services:
  hfr-service:
    image: opengpunetwork/hfr-client:latest
    pull_policy: always
    ports:
      - "${PORT}:5555"
    extra_hosts: 
      - "host.docker.internal:host-gateway"
    environment:
      - CALLBACK_URL=${CALLBACK_URL}
      - 'PIPE_ARGS_STR={"task": "visual-question-answering", "model": "dandelin/vilt-b32-finetuned-vqa"}'
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    networks:
      - app_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

networks:
  app_network:
    driver: bridge

volumes:
  huggingface_cache:
```

### Step 3: Host Your Docker Compose File

Upload your Docker Compose file to a **publicly accessible URL**:

- GitHub raw URL (recommended)
- Your own web server
- CDN or file hosting service

### Step 4: Publish Your Source

```python
import ogpu.client
from web3 import Web3

# Configure chain
ogpu.client.ChainConfig.set_chain(ogpu.client.ChainId.OGPU_TESTNET)

# Create your Hugging Face source
source_info = ogpu.client.SourceInfo(
    name="VQA Model Service",
    description="Visual Question Answering using dandelin/vilt-b32-finetuned-vqa",
    logoUrl="https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.png",
    imageEnvs=ogpu.client.ImageEnvironments(
        nvidia="https://raw.githubusercontent.com/yourusername/your-repo/main/docker-compose-gpu.yml"
    ),
    minPayment=Web3.to_wei(0.001, "ether"),
    minAvailableLockup=Web3.to_wei(0, "ether"),
    maxExpiryDuration=86400,
    deliveryMethod=ogpu.client.DeliveryMethod.FIRST_RESPONSE
)

# Publish source
source_address = ogpu.client.publish_source(source_info)
print(f"✅ Source published: {source_address}")
```

## 🎯 Supported Models

The Hugging Face Ready environment works with **any model** that supports Hugging Face's high-level pipeline interface. Simply specify the `task` and `model` in your `PIPE_ARGS_STR` configuration.

**Examples:**
- Text models: GPT-2, BERT, RoBERTa, T5, etc.
- Vision models: ViT, DETR, ResNet, etc.  
- Audio models: Wav2Vec2, Whisper, etc.
- Multimodal models: CLIP, LayoutLM, etc.

Browse the [Hugging Face Hub](https://huggingface.co/models) to find models for your specific use case.

## ⚙️ Configuration Examples

### Text Classification Example

```yaml
services:
  hfr-service:
    image: opengpunetwork/hfr-client:latest
    pull_policy: always
    ports:
      - "${PORT}:5555"
    extra_hosts: 
      - "host.docker.internal:host-gateway"
    environment:
      - CALLBACK_URL=${CALLBACK_URL}
      - 'PIPE_ARGS_STR={"task": "text-classification", "model": "cardiffnlp/twitter-roberta-base-sentiment-latest"}'
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    networks:
      - app_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

networks:
  app_network:
    driver: bridge

volumes:
  huggingface_cache:
```

### Image Classification Example

```yaml
services:
  hfr-service:
    image: opengpunetwork/hfr-client:latest
    pull_policy: always
    ports:
      - "${PORT}:5555"
    extra_hosts: 
      - "host.docker.internal:host-gateway"
    environment:
      - CALLBACK_URL=${CALLBACK_URL}
      - 'PIPE_ARGS_STR={"task": "image-classification", "model": "google/vit-base-patch16-224"}'
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    networks:
      - app_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

networks:
  app_network:
    driver: bridge

volumes:
  huggingface_cache:
```

### Text Generation Example

```yaml
services:
  hfr-service:
    image: opengpunetwork/hfr-client:latest
    pull_policy: always
    ports:
      - "${PORT}:5555"
    extra_hosts: 
      - "host.docker.internal:host-gateway"
    environment:
      - CALLBACK_URL=${CALLBACK_URL}
      - 'PIPE_ARGS_STR={"task": "text-generation", "model": "gpt2"}'
    volumes:
      - huggingface_cache:/root/.cache/huggingface
    networks:
      - app_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

networks:
  app_network:
    driver: bridge

volumes:
  huggingface_cache:
```


## 📊 Testing Your Source with Using Swagger UI

Once your source is running locally, visit:
```
http://localhost:5555/docs
```

Ready to deploy AI models! 🚀

---

## 🎯 Next Step: Create Tasks for Your Source

Now that you have a HuggingFace source running, learn how to publish tasks that use it:

**[📋 HuggingFace Task Creation →](../../tasks/templates/huggingface-pipeline.md)**

The task template will show you how to:

- ✅ Configure task parameters for your HuggingFace models
- ✅ Set up proper input/output handling
- ✅ Define payment and timeout settings
- ✅ Handle task responses and validation
