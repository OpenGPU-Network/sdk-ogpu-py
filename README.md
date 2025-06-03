# 🧠 OpenGPU SDK

Welcome to the edge of distributed AI.

The `ogpu.service` SDK lets you write **task handlers** that will run **on remote provider machines** — not your laptop.  
You define what your task expects and yapar, and we handle the wiring, serving, and background magic.

> ✨ Write your task. 🛰️ Deploy it. ⚡️ Let the network run it.

---

## 🚀 What is this?

This SDK is used by **client developers** to write Python **tasks** (as functions) that will be deployed and executed **on OpenGPU network providers**.

Your code will:
- Accept inputs (Pydantic model)
- Process them inside a registered **task handler**
- Expose a `/run/{task}/{task_address}` endpoint via FastAPI
- Be served by remote compute

---

## 🧪 Example: Your First Task

```python
import ogpu.service
from pydantic import BaseModel

class MultiplyInput(BaseModel):
    a: int
    b: int

class MultiplyOutput(BaseModel):
    result: int

@ogpu.service.expose()
def multiply(data: MultiplyInput) -> MultiplyOutput:
    ogpu.service.logger.info(f"🧮 Starting multiplication: {data.a} * {data.b}")
    result = data.a * data.b
    ogpu.service.logger.info(f"✅ Result computed: {result}")
    return MultiplyOutput(result=result)

ogpu.service.start()
```

That’s it.
This exposes an endpoint at:

```
POST /run/multiply/{task_address}
```

With body:
```json
{
  "a": 5,
  "b": 7
}
```

---

## 📡 How It Works

- `@expose()`: Marks your function as a **task handler**.
- `start()`: Starts a FastAPI server that awaits tasks.
- Your task runs in a background thread.
- The result is logged, not returned over HTTP.

---

## 🧙 Guidelines

- Your task handler must accept **one** `pydantic.BaseModel` input
- It must return another `pydantic.BaseModel`
- Task (function) names must be **unique**
- Output will be logged to the console — keep it clean 💅

---

## 🤝 Made for the OpenGPU Network  
Unleash your code. Let the grid handle the rest.