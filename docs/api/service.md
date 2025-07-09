# API Reference: ogpu.service

Essential API reference for the `ogpu.service` module - the foundation for building **custom AI services** on the OpenGPU network.

!!! info "Custom Source Development"
    **This module is designed for creating custom AI sources.** Use `ogpu.service` to build your own AI services that can be deployed as sources on the OpenGPU network.

## 🎯 Essential Functions

The `ogpu.service` module provides three core functions for custom source development:

- **`@init()`** - Initialize AI models and resources during service startup
- **`@expose()`** - Make your AI functions available as network services  
- **`start()`** - Launch your service to handle OpenGPU network tasks
- **`logger`** - Built-in logging with Sentry integration for production monitoring

::: ogpu.service.decorators.init
    options:
      show_source: true
      heading_level: 2
      show_root_heading: true

**Purpose:** Initialize AI models and expensive resources when your service starts, before handling any tasks.

```python
import ogpu.service
from transformers import AutoTokenizer, AutoModel

# Global variables for loaded models
tokenizer = None
model = None

@ogpu.service.init()
def setup_ai_models():
    """Load AI models during service startup."""
    global tokenizer, model
    
    try:
        ogpu.service.logger.info("🔄 Loading sentiment analysis model...")
        
        tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
        model = AutoModel.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
        
        ogpu.service.logger.info("✅ Models loaded successfully!")
        
    except Exception as e:
        ogpu.service.logger.error(f"❌ Model loading failed: {e}")
        raise  # Stop service startup if models fail to load
```

**Key Points:**
- Only one `@init()` function per service
- Runs once when service starts, before handling tasks
- Use for loading AI models, connecting to databases, etc.
- **Always use `ogpu.service.logger`** for startup monitoring

::: ogpu.service.decorators.expose
    options:
      show_source: true
      heading_level: 2
      show_root_heading: true

**Purpose:** Transform your AI functions into network-accessible services that can receive tasks from the OpenGPU network.

```python
from pydantic import BaseModel
import ogpu.service

class TextInput(BaseModel):
    text: str
    model_name: str = "default"

class SentimentOutput(BaseModel):
    sentiment: str
    confidence: float

@ogpu.service.expose()
def analyze_sentiment(data: TextInput) -> SentimentOutput:
    """Custom sentiment analysis service."""
    ogpu.service.logger.info(f"📝 Processing text: '{data.text[:30]}...'")
    
    try:
        # Your AI model logic here (model loaded from @init())
        result = custom_sentiment_model.predict(data.text, data.model_name)
        
        ogpu.service.logger.info("✅ Sentiment analysis completed")
        return SentimentOutput(
            sentiment=result.label,
            confidence=result.score
        )
        
    except Exception as e:
        ogpu.service.logger.error(f"❌ Inference failed: {e}", extra={
            "input_text": data.text[:100],
            "model_name": data.model_name
        })
        raise

@ogpu.service.expose(timeout=300)  # 5 minutes for heavy models
def generate_image(data: ImagePrompt) -> ImageOutput:
    """Custom image generation service."""
    # Heavy model inference
    image_data = custom_diffusion_model.generate(data.prompt)
    return ImageOutput(image_base64=image_data)
```

**Key Requirements:**
- Input/output types **must** be Pydantic `BaseModel` subclasses
- Function names become API endpoints (e.g., `analyze_sentiment` → `/run/analyze_sentiment/...`)
- **Always use `ogpu.service.logger`** for task monitoring

::: ogpu.service.server.start
    options:
      show_source: true
      heading_level: 2
      show_root_heading: true

**Purpose:** Start your custom AI service server to handle OpenGPU network tasks.

```python
#!/usr/bin/env python3
"""Complete custom service example."""

import ogpu.service
from pydantic import BaseModel
from transformers import pipeline

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    label: str
    score: float

classifier = None

@ogpu.service.init()
def load_model():
    """Load sentiment analysis model on startup."""
    global classifier
    ogpu.service.logger.info("🔄 Starting model initialization...")
    
    try:
        classifier = pipeline("sentiment-analysis", 
                             model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        ogpu.service.logger.info("✅ Sentiment model loaded successfully!")
        
    except Exception as e:
        ogpu.service.logger.error(f"❌ Failed to load model: {e}")
        raise  # Service won't start if model loading fails

@ogpu.service.expose(timeout=60)
def analyze_sentiment(data: SentimentRequest) -> SentimentResponse:
    """Analyze sentiment of input text."""
    ogpu.service.logger.info(f"📝 Analyzing text: '{data.text[:50]}{'...' if len(data.text) > 50 else ''}'")
    
    try:
        result = classifier(data.text)[0]
        
        ogpu.service.logger.info(f"✅ Analysis complete: {result['label']} (confidence: {result['score']:.3f})")
        
        return SentimentResponse(
            label=result['label'],
            score=result['score']
        )
        
    except Exception as e:
        # This error will appear in your Sentry dashboard!
        ogpu.service.logger.error(f"❌ Sentiment analysis failed: {e}", extra={
            "input_text": data.text[:100],
            "input_length": len(data.text),
            "model": "twitter-roberta-base-sentiment-latest"
        })
        raise  # Re-raise to return error to client

if __name__ == "__main__":
    ogpu.service.logger.info("🚀 Starting sentiment analysis service...")
    ogpu.service.start()
```

**Generated Endpoints:**

- `POST /run/{function_name}/{task_address}` - Your exposed functions
- `GET /docs` - Interactive API documentation (Swagger UI)

## logger - Sentry Integration

**Purpose:** Built-in logging with automatic Sentry integration for production monitoring and error tracking.

```python
import ogpu.service

# Basic logging
ogpu.service.logger.info("Model loaded successfully")
ogpu.service.logger.warning("Low confidence prediction")
ogpu.service.logger.error("Model inference failed")

# Detailed logging with context
ogpu.service.logger.error(f"Failed to process input: {data}", extra={"task_id": task_id})
```

!!! tip "Sentry Integration Benefits"
    **Why use `ogpu.service.logger`?**
    
    - ✅ **Error Tracking**: Failed tasks automatically appear in your Sentry dashboard
    - ✅ **Performance Monitoring**: Track inference times and bottlenecks  
    - ✅ **Real-time Alerts**: Get notified when your service has issues
    - ✅ **Context**: See exactly what input caused failures
    - ✅ **Production Ready**: Built-in integration with OpenGPU monitoring

**Best Practice Example:**

```python
@ogpu.service.expose(timeout=60)
def analyze_sentiment(data: SentimentRequest) -> SentimentResponse:
    """Analyze sentiment with proper logging."""
    try:
        ogpu.service.logger.info(f"Analyzing text: {data.text[:50]}...")
        
        # Your model inference
        result = classifier(data.text)[0]
        
        ogpu.service.logger.info(f"Analysis complete: {result['label']} ({result['score']:.3f})")
        
        return SentimentResponse(label=result['label'], score=result['score'])
        
    except Exception as e:
        # This error will appear in Sentry dashboard!
        ogpu.service.logger.error(f"Sentiment analysis failed: {e}", extra={
            "input_text": data.text[:100],
            "model_name": "sentiment-classifier"
        })
        raise
```