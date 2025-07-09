# Sources Overview

Sources in OpenGPU are the foundation for publishing and managing your computational tasks on the decentralized network. A source defines the container environment, payment structure, and delivery method for your tasks.

## 🎯 What is a Source?

A **Source** is essentially a configuration template that specifies:

- **Container Environments**: Public URLs to Docker Compose files defining service infrastructure
- **Payment Settings**: Minimum payment requirements and lockup amounts
- **Delivery Method**: How task results are delivered and confirmed
- **Metadata**: Name, description, and branding information

## 🏗️ Source Components

### Image Environments
Sources support multiple hardware environments through **public URLs** to Docker Compose files:

- **CPU**: Standard CPU-based processing
- **NVIDIA**: NVIDIA GPU acceleration  
- **AMD**: AMD GPU acceleration

!!! info "Technical Implementation"
    OpenGPU sources use **public URLs** pointing to Docker Compose files, not direct Docker image references. This allows for complete infrastructure definition including networking, volumes, and multi-service deployments.

### Delivery Methods
Choose how task results are handled:

- **Manual Confirmation**: Client manually confirms responses
- **First Response**: First valid response is automatically accepted

### Payment Structure
Configure economic parameters:

- **Minimum Payment**: Base payment for task execution
- **Minimum Lockup**: Required stake from providers
- **Expiry Duration**: Maximum time for task completion

## 🚀 Getting Started

Choose your path based on your needs:

## 🎯 Two Ways to Create Sources

There are **two approaches** to create sources on OpenGPU:

### 🚀 Method 1: Pre-built Templates  
Use ready-made source templates provided by OpenGPU. These templates offer zero-configuration deployment for popular frameworks and use cases.

**Perfect for:**

- AI/ML tasks using popular frameworks
- Standard data processing workflows  
- Quick prototyping and testing
- Production-ready configurations

**Benefits:**

- ⚡ Setup in minutes
- 🛡️ Maintained by OpenGPU team
- 📊 Proven and tested environments
- ❌ No Docker knowledge required

**Get Started:**
- **[Source Templates →](templates/index.md)** - Browse available templates
- **[Hugging Face Pipeline →](templates/huggingface-pipeline.md)** - AI/ML template example

### 🔧 Method 2: Custom Sources
Build and deploy your own Docker containers with custom logic, dependencies, and configurations. Perfect for specialized workloads and custom services.


**Perfect for:**

- Custom algorithms and specialized processing
- Proprietary models and business logic
- Specific hardware optimizations
- Complex multi-service architectures


**Benefits:**

- 🚀 Maximum flexibility and control
- 🎛️ Custom business logic implementation
- 💪 Specialized hardware optimizations
- 🔧 Complete environment customization


**Get Started:**

- **[Custom Sources Guide →](custom-sources.md)** - Build your own services

!!! tip "Which Approach to Choose?"
    - **Pre-built Templates**: Quick setup, no Docker required, proven configurations
    - **Custom Sources**: Maximum flexibility, custom logic, specialized dependencies


## 🔄 Source Lifecycle

1. **Create**: Define source configuration and metadata
2. **Publish**: Deploy source to the blockchain
3. **Use**: Reference source when publishing tasks
4. **Update**: Modify source parameters as needed


## 🎯 Next Steps

- **[Configuration](configuration.md)** - Configure and publish your sources
- **[Source Templates](templates/index.md)** - Browse pre-built templates  
- **[Custom Sources](custom-sources.md)** - Build specialized services
- **[Publishing Tasks](../tasks/publishing-tasks.md)** - Learn to use your sources for tasks