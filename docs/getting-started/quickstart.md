# Quick Start Guide

Get your first OpenGPU task up and running in just a few minutes! This guide will walk you through creating, deploying, and running a simple task.

## 🎯 What We'll Build

We'll create a simple task that multiplies two numbers and deploy it on the OpenGPU network.

---

## 📋 Prerequisites

Before we start, make sure you have:

- ✅ **OpenGPU SDK installed** ([Installation Guide](installation.md))
- ✅ **Python 3.8+** running
- ✅ **Text editor** or IDE ready

---

## 🏗️ Step 1: Create Your Task Handler

Create a new file called `my_first_task.py`:

```python
import ogpu.service
from pydantic import BaseModel

# Define input and output data models
class MultiplyInput(BaseModel):
    a: int
    b: int

class MultiplyOutput(BaseModel):
    result: int
    message: str

# Create your task handler
@ogpu.service.expose()
def multiply_numbers(input_data: MultiplyInput) -> MultiplyOutput:
    """
    A simple task that multiplies two numbers.
    """
    result = input_data.a * input_data.b
    message = f"{input_data.a} × {input_data.b} = {result}"
    
    return MultiplyOutput(
        result=result,
        message=message
    )

if __name__ == "__main__":
    print("🚀 Starting OpenGPU service...")
    ogpu.service.start()
```

### What's Happening Here?

1. **Import**: We import the OpenGPU service module and Pydantic for data models
2. **Models**: We define input and output data structures using Pydantic BaseModel
3. **Decorator**: The `@ogpu.service.expose()` decorator registers our function as a task
4. **Function**: Our task logic - simple multiplication with a descriptive message
5. **Serve**: `ogpu.service.start()` starts the service and makes it available on the network

---

## 🚀 Step 2: Start Your Service

Run your service to make it available on the OpenGPU network:

```bash
python my_first_task.py
```

!!! tip "Keep It Running"
    Leave this terminal window open. Your service needs to be running to receive and process tasks.

### 🌐 Quick Test with REST API Documentation

Once your service is running, you can immediately test it using the built-in API documentation:

1. **Open your browser** and navigate to: `http://localhost:5555/docs`
2. **Explore the API** - You'll see an interactive Swagger UI with your task endpoints
3. **Test directly** - Click on your `multiply_numbers` endpoint and use the "Try it out" button
4. **Send a request** - Use the example payload:
   ```json
   {
     "a": 15,
     "b": 7
   }
   ```

!!! success "Interactive Testing"
    The `/docs` endpoint provides a complete interactive interface where you can test your tasks without writing any client code!

---

## 🎯 What's Next?

Congratulations! You've successfully:

- ✅ Created your first OpenGPU task
- ✅ Published and retrieved task results

### Learn More

**Essential Topics:**

- **[Nonce Management](../advanced/nonce-management.md)** - Handle transaction errors and stuck transactions
- **[Task Configuration](../tasks/configuration.md)** - Advanced task settings
- **[Custom Sources](../sources/custom-sources.md)** - Create your own task sources

### Real-World Examples

Try building these next:

- **Image Processing**: Resize, filter, or analyze images
- **Data Analysis**: Process CSV files or perform calculations
- **AI Models**: Deploy machine learning inference tasks
- **Web Scraping**: Extract and process web data

---

## 🆘 Need Help?

- **Documentation**: You're reading it! Check other sections for advanced topics
- **GitHub Issues**: [Report bugs or ask questions](https://github.com/OpenGPU-Network/sdk-ogpu-py/issues)
- **Community**: Join discussions and get help from other developers

Happy building with OpenGPU! 🚀
