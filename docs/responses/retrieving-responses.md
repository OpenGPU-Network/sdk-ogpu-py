# Retrieving Responses

Learn how to fetch and monitor task responses from providers on the OpenGPU network.

## 🎯 Overview

When providers complete your tasks, they submit responses containing:

- **Result Data**: The computed output
- **Provider Info**: Who executed the task
- **Status**: Submitted/confirmed indicators
- **Timestamps**: When work was completed

## 📥 Basic Response Retrieval

### Get All Responses for a Task

```python
import ogpu.client

# Get all responses for a task
task_address = "0x1234567890abcdef..."
responses = ogpu.client.get_task_responses(task_address)

print(f"📨 Found {len(responses)} responses")

for i, response in enumerate(responses):
    print(f"\n--- Response {i+1} ---")
    print(f"Provider: {response.provider}")
    print(f"Status: {response.status}")
    print(f"Data: {response.data}")
    print(f"Confirmed: {response.confirmed}")
    print(f"Timestamp: {response.timestamp}")
```

### Check for Confirmed Response

```python
def get_confirmed_result(task_address: str):
    """Get the confirmed response result"""
    try:
        confirmed_response = ogpu.client.get_confirmed_response(task_address)
        
        if confirmed_response:
            print("✅ Task completed with confirmed result:")
            print(f"📝 Result: {confirmed_response.data}")
            print(f"👤 Provider: {confirmed_response.provider}")
            return confirmed_response.data
        else:
            print("⏳ No confirmed response yet")
            return None
            
    except Exception as e:
        print(f"❌ Error retrieving confirmed response: {e}")
        return None
```

## 🔍 Real-time Response Monitoring

### Basic Monitoring

```python
import time

def monitor_task_responses(task_address: str, timeout: int = 3600):
    """Monitor task for responses in real-time"""
    start_time = time.time()
    last_response_count = 0
    
    print(f"🔍 Monitoring task: {task_address}")
    
    while time.time() - start_time < timeout:
        try:
            responses = ogpu.client.get_task_responses(task_address)
            
            # Check for new responses
            if len(responses) > last_response_count:
                new_responses = responses[last_response_count:]
                
                for response in new_responses:
                    print(f"📨 New response from {response.provider}")
                    print(f"📝 Data: {response.data}")
                    
                last_response_count = len(responses)
            
            # Check if task is confirmed
            confirmed = ogpu.client.get_confirmed_response(task_address)
            if confirmed:
                print(f"✅ Task confirmed! Result: {confirmed.data}")
                return confirmed.data
            
            print(f"⏳ Waiting... ({len(responses)} responses so far)")
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(10)
    
    print("⏰ Monitoring timeout reached")
    return None
```

### Advanced Monitoring with Callbacks

```python
def monitor_with_callback(task_address: str, on_new_response=None, on_confirmed=None):
    """Monitor with custom callback functions"""
    responses_seen = set()
    
    while True:
        try:
            responses = ogpu.client.get_task_responses(task_address)
            
            # Check for new responses
            for response in responses:
                if response.address not in responses_seen:
                    responses_seen.add(response.address)
                    if on_new_response:
                        on_new_response(response)
            
            # Check for confirmation
            confirmed = ogpu.client.get_confirmed_response(task_address)
            if confirmed:
                if on_confirmed:
                    on_confirmed(confirmed)
                break
                
            time.sleep(15)  # Check every 15 seconds
            
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(10)

# Usage example
def on_response(response):
    print(f"📨 New response: {response.data[:100]}...")

def on_confirm(confirmed_response):
    print(f"✅ Task confirmed: {confirmed_response.data}")

monitor_with_callback(task_address, on_response, on_confirm)
```