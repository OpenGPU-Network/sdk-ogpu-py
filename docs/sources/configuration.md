# Configuration

Learn how to configure and publish sources on the OpenGPU network. This guide covers the configuration parameters and publishing process that apply to both pre-built environments and custom sources.

## 📋 Prerequisites

Before configuring any source, ensure you have:

- ✅ **OpenGPU SDK installed** ([Installation Guide](../getting-started/installation.md))
- ✅ **Wallet configured** with private key in environment variables
- ✅ **Chain configuration** set up (testnet or mainnet)
- ✅ **Sufficient OGPU** for gas fees in your wallet

### Environment Setup

```bash
# Set your private key
export CLIENT_PRIVATE_KEY="your_private_key_here"

# Verify installation
python -c "import ogpu.client; print('OpenGPU SDK ready!')"
```

---

## 🔧 SourceInfo Configuration

Both pre-built and custom sources use the same `SourceInfo` structure:

```python
import ogpu.client
from web3 import Web3

source_info = ogpu.client.SourceInfo(
    name="my-service",                              # Human-readable name
    description="Service description",              # Detailed description
    logoUrl="https://example.com/logo.png",        # Optional logo URL
    imageEnvs=ogpu.client.ImageEnvironments(       # Container environments
        cpu="https://public-url/docker-compose-cpu.yml",
        nvidia="https://public-url/docker-compose-gpu.yml"
    ),
    minPayment=Web3.to_wei(0.01, "ether"),         # Minimum payment
    maxExpiryDuration=3600,                        # Maximum execution time (seconds)
    deliveryMethod=ogpu.client.DeliveryMethod.FIRST_RESPONSE,  # Result delivery method
    minAvailableLockup=Web3.to_wei(0, "ether")    # Optional: required provider stake
)
```

## 📊 Configuration Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | `str` | Human-readable source name | `"sentiment-analyzer"` |
| `description` | `str` | Detailed source description | `"AI sentiment analysis service"` |
| `logoUrl` | `str` | URL to source logo/icon | `"https://example.com/logo.png"` |
| `imageEnvs` | `ImageEnvironments` | Public URLs to Docker Compose files | See examples below |
| `minPayment` | `int` | Minimum payment in wei | `Web3.to_wei(0.01, "ether")` |
| `maxExpiryDuration` | `int` | Maximum execution time in seconds | `3600` (1 hour) |
| `deliveryMethod` | `DeliveryMethod` | How results are delivered | `FIRST_RESPONSE` or `MANUAL_CONFIRMATION` |
| `minAvailableLockup` | `int` | Required provider stake in wei (optional) | `Web3.to_wei(0.1, "ether")` |

---

## 🖥️ Image Environments

The `ImageEnvironments` specifies **public URLs** to Docker Compose files for different hardware:

### Single Environment (CPU Only)

```python
imageEnvs = ogpu.client.ImageEnvironments(
    cpu="https://cipfs.ogpuscan.io/ipfs/QmYourCPUCompose"
)
```

### Multi-Environment with GPU Support

```python
imageEnvs = ogpu.client.ImageEnvironments(
    cpu="https://cipfs.ogpuscan.io/ipfs/QmYourCPUCompose",
    nvidia="https://cipfs.ogpuscan.io/ipfs/QmYourGPUCompose",
    amd="https://cipfs.ogpuscan.io/ipfs/QmYourAMDCompose"
)
```

!!! important "Public URLs Required"
    Each URL must point to a publicly accessible Docker Compose file that defines:
    - The container image to use
    - Environment variables and configuration  
    - Port mappings (must expose port 5555)
    - Volume mounts if needed

### Environment Selection Guidelines

- **CPU**: Always include for maximum compatibility
- **NVIDIA**: Include for CUDA-accelerated workloads  
- **AMD**: Include for ROCm-accelerated workloads

---

## 💰 Payment Configuration

Configure economic parameters for your source:

### Basic Payment Setup

```python
# Basic payment setup
minPayment = Web3.to_wei(0.01, "ether")      # 0.01 OGPU minimum

# Alternative units
minPayment = Web3.to_wei(10, "gwei")         # 10 Gwei  
minPayment = 1000000000000000000              # 1 OGPU in wei (direct)
```

### Provider Stake Requirements

```python
# Require provider stake (optional)
minAvailableLockup = Web3.to_wei(0.1, "ether")  # Providers must stake 0.1 OGPU
```

---

## 📡 Delivery Methods

Choose how task results are handled:

### Automatic Acceptance

```python
# First valid response is accepted automatically
deliveryMethod = ogpu.client.DeliveryMethod.FIRST_RESPONSE
```

**Use when:**
- Results are deterministic
- You trust the provider network
- You want faster task completion

### Manual Confirmation

```python
# Client must approve results manually
deliveryMethod = ogpu.client.DeliveryMethod.MANUAL_CONFIRMATION
```

**Use when:**
- Results need human review
- Quality control is important
- Tasks are high-value or critical

---

## 🚀 Publishing Your Source

Configure and publish your source to the OpenGPU network:

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
    source_address = ogpu.client.publish_source(source_info)
    print(f"✅ Source published successfully!")
    print(f"Source address: {source_address}")
except Exception as e:
    print(f"❌ Failed to publish source: {e}")
```

### Private Key Configuration

The SDK automatically uses your private key from environment variables:

```bash
export CLIENT_PRIVATE_KEY="your_private_key_here"
```

Or pass it explicitly:

```python
source_address = ogpu.client.publish_source(
    source_info=source_info,
    private_key="your_private_key_here"
)
```

---

## 🔧 Validation Checklist

- ✅ Docker Compose files are publicly accessible via HTTPS URLs
- ✅ Private key is configured correctly
- ✅ Wallet has sufficient $OGPU for gas
- ✅ Chain configuration matches your target network
- ✅ Docker Compose files are valid YAML and contain required services
- ✅ Payment amounts are competitive with network rates
- ✅ Timeout durations are reasonable for your use case

---

## 🎯 Configuration Examples

### Quick Start Configuration

```python
# Simple configuration for testing
simple_source = ogpu.client.SourceInfo(
    name="test-service",
    description="Simple test service",
    imageEnvs=ogpu.client.ImageEnvironments(
        cpu="https://cipfs.ogpuscan.io/ipfs/QmTestCompose"
    ),
    minPayment=Web3.to_wei(0.001, "ether"),
    maxExpiryDuration=300,  # 5 minutes
    deliveryMethod=ogpu.client.DeliveryMethod.FIRST_RESPONSE
)
```

### Production Configuration

```python
# Production-ready configuration
production_source = ogpu.client.SourceInfo(
    name="ai-image-processor",
    description="High-performance AI image processing service",
    logoUrl="https://mycompany.com/logo.png",
    imageEnvs=ogpu.client.ImageEnvironments(
        cpu="https://cipfs.ogpuscan.io/ipfs/QmProdCPUCompose",
        nvidia="https://cipfs.ogpuscan.io/ipfs/QmProdGPUCompose"
    ),
    minPayment=Web3.to_wei(0.02, "ether"),
    minAvailableLockup=Web3.to_wei(0.1, "ether"),
    maxExpiryDuration=1800,  # 30 minutes
    deliveryMethod=ogpu.client.DeliveryMethod.MANUAL_CONFIRMATION
)
```

---

## 🎯 Next Steps

### After Configuration:
- **[Hugging Face Pipeline](templates/huggingface-pipeline.md)** - Configure pre-built AI/ML environments
- **[Custom Sources](custom-sources.md)** - Build specialized custom services
- **[Publishing Tasks](../tasks/publishing-tasks.md)** - Start using your configured sources

### Advanced Topics:
- **[API Reference](../api/client.md)** - Complete API documentation

---

## 🆘 Need Help?

- **[GitHub Examples](https://github.com/OpenGPU-Network/sdk-ogpu-py/tree/main/examples)** - Reference implementations
- **[Issues](https://github.com/OpenGPU-Network/sdk-ogpu-py/issues)** - Report problems or ask questions
- **[Documentation](../index.md)** - Browse all guides

Happy configuring! 🚀