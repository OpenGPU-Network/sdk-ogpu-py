# Installation Guide

This guide will help you install and set up the OpenGPU SDK in your Python environment.

## Prerequisites

- **Python 3.8 or higher**
- **pip package manager**
- **Git** (for development installation)

## 🚀 Quick Installation

### Standard Installation

Install the OpenGPU SDK using pip:

```bash
pip install ogpu
```

### Virtual Environment (Recommended)

We strongly recommend using a virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv ogpu-env

# Activate virtual environment
# On Linux/Mac:
source ogpu-env/bin/activate

# On Windows:
ogpu-env\Scripts\activate

# Install the SDK
pip install ogpu
```

### Using conda

If you prefer conda:

```bash
# Create conda environment
conda create -n ogpu-env python=3.8

# Activate environment
conda activate ogpu-env

# Install the SDK
pip install ogpu
```

---

## 🔧 Development Installation

For contributors or those needing the latest development features:

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/OpenGPU-Network/sdk-ogpu-py.git
cd sdk-ogpu-py

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Development Dependencies

The development installation includes additional tools:

- **pytest**: For running tests
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Type checking
- **sphinx**: Documentation generation

---

## ⚙️ Environment Configuration

### Setup Your Environment

Create a `.env` file in your project directory to store your configuration:

```bash
# Create .env file
touch .env
```

Add your private key to the `.env` file:

```env
# .env
CLIENT_PRIVATE_KEY=your_private_key_here
```

The SDK will automatically load environment variables from the `.env` file when you run your application.

!!! warning "Security Note"
    Never commit your `.env` file to version control. Add `.env` to your `.gitignore` file.

---

## ✅ Verify Installation

Test that everything is working correctly:

```python
import ogpu

# Check version
print(f"OpenGPU SDK version: {ogpu.__version__}")

# Test basic imports
from ogpu.service import task
from ogpu.client import OGPUClient

print("✅ OpenGPU SDK installed successfully!")
```

---


## 🗑️ Uninstallation

To remove the OpenGPU SDK:

```bash
pip uninstall ogpu
```

---

## ⏭️ Next Steps

Now that you have the SDK installed, let's create your first task:

👉 **[Quick Start Guide](quickstart.md)** - Build your first OpenGPU task in minutes
