# Confirming Responses

Learn how to validate, review, and confirm task responses to complete the task lifecycle on the OpenGPU network.

!!! warning "Delivery Method Controls Confirmation"
    **Important**: Response confirmation behavior depends on your source's **delivery method** configuration:
    
    - **`FIRST_RESPONSE`**: The first submitted response is **automatically confirmed** - no manual action needed
    - **`MANUAL_CONFIRMATION`**: You **must manually confirm** responses using the methods below
    
    Check your source configuration to understand which delivery method is active for your tasks.


## 🎯 Overview

Response confirmation is the final step in the task lifecycle. Once you confirm a response:

- ✅ **Payment Released**: Provider receives OGPU tokens
- ✅ **Task Completed**: Task moves to completed state  
- ✅ **Result Finalized**: Response becomes the official result
- ❌ **No Changes**: Confirmation cannot be undone


## ✅ Manual Confirmation

### Review and Confirm Manually

```python
import ogpu.client

def confirm_response_manually(task_address: str):
    """Manually confirm a response after review"""
    responses = ogpu.client.get_task_responses(task_address)
    
    if not responses:
        print("❌ No responses found")
        return
    
    # Review responses
    for i, response in enumerate(responses):
        print(f"\n--- Response {i+1} ---")
        print(f"Provider: {response.provider}")
        print(f"Data: {response.data}")
        print(f"Status: {response.status}")
        
        # Ask user to confirm
        choice = input("Confirm this response? (y/n): ")
        
        if choice.lower() == 'y':
            try:
                confirmation_tx = ogpu.client.confirm_response(response.address)
                print(f"✅ Response confirmed!")
                print(f"📍 Transaction: {confirmation_tx}")
                return response.data
            except Exception as e:
                print(f"❌ Confirmation failed: {e}")
    
    print("❌ No response confirmed")
    return None
```

### Interactive Response Selection

```python
def interactive_confirmation(task_address: str):
    """Interactive response selection and confirmation"""
    responses = ogpu.client.get_task_responses(task_address)
    
    if not responses:
        print("❌ No responses found")
        return None
    
    # Display all responses
    print(f"📋 Available responses ({len(responses)}):")
    
    for i, response in enumerate(responses, 1):
        print(f"\n{i}. Provider: {response.provider}")
        print(f"   Status: {response.status}")
        print(f"   Length: {len(response.data)} characters")
        print(f"   Preview: {response.data[:100]}...")
    
    # Get user choice
    while True:
        try:
            choice = input(f"\nSelect response to confirm (1-{len(responses)}, or 'q' to quit): ")
            
            if choice.lower() == 'q':
                print("❌ Confirmation cancelled")
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(responses):
                selected_response = responses[index]
                
                # Show full response for final review
                print(f"\n📝 Full response from {selected_response.provider}:")
                print(f"{selected_response.data}")
                
                confirm = input("\nConfirm this response? (y/n): ")
                if confirm.lower() == 'y':
                    confirmation_tx = ogpu.client.confirm_response(selected_response.address)
                    print(f"✅ Response confirmed!")
                    print(f"📍 Transaction: {confirmation_tx}")
                    return selected_response.data
                    
            else:
                print("❌ Invalid selection")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except Exception as e:
            print(f"❌ Confirmation error: {e}")
    
    return None
```

## 🤖 Automatic Confirmation

### Auto-confirm First Successful Response

```python
def auto_confirm_first_submitted(task_address: str):
    """Automatically confirm the first submitted response"""
    responses = ogpu.client.get_task_responses(task_address)
    
    # Filter submitted responses
    submitted_responses = [r for r in responses if r.status == "submitted"]
    
    if not submitted_responses:
        print("❌ No submitted responses found")
        return None
    
    # Choose first submitted response
    best_response = submitted_responses[0]
    
    try:
        confirmation_tx = ogpu.client.confirm_response(best_response.address)
        print(f"✅ Auto-confirmed first submitted response")
        print(f"👤 Provider: {best_response.provider}")
        print(f"📍 Transaction: {confirmation_tx}")
        return best_response.data
    except Exception as e:
        print(f"❌ Auto-confirmation failed: {e}")
        return None
```

### Auto-confirm with Quality Validation

```python
def auto_confirm_with_validation(task_address: str):
    """Auto-confirm response only if it passes quality validation"""
    responses = ogpu.client.get_task_responses(task_address)
    
    for response in responses:
        if response.status == "submitted":
            if validate_response_quality(response.data):
                try:
                    confirmation_tx = ogpu.client.confirm_response(response.address)
                    print(f"✅ Valid response auto-confirmed!")
                    print(f"👤 Provider: {response.provider}")
                    return response.data
                except Exception as e:
                    print(f"❌ Confirmation failed: {e}")
            else:
                print(f"❌ Response from {response.provider} failed quality check")
    
    print("❌ No valid responses found for auto-confirmation")
    return None

def validate_response_quality(response_data: str) -> bool:
    """Validate response quality before confirmation"""
    checks = [
        len(response_data) > 10,  # Minimum length
        not response_data.startswith("Error"),  # Not an error message
        len(response_data.split()) > 2,  # Multiple words
        not any(word in response_data.lower() for word in ["failed", "timeout", "error"])  # No error keywords
    ]
    
    score = sum(checks)
    quality = score / len(checks)
    
    print(f"📊 Response quality score: {quality:.2f}")
    return quality >= 0.75  # 75% threshold
```

## 🏆 Best Response Selection

### Score-based Selection

```python
def confirm_best_scored_response(task_address: str):
    """Confirm response with highest quality score"""
    responses = ogpu.client.get_task_responses(task_address)
    
    if not responses:
        print("❌ No responses found")
        return None
    
    submitted_responses = [r for r in responses if r.status == "submitted"]
    
    if not submitted_responses:
        print("❌ No submitted responses found")
        return None
    
    # Score all submitted responses
    scored_responses = []
    for response in submitted_responses:
        score = calculate_response_score(response.data)
        scored_responses.append((response, score))
        print(f"📊 {response.provider}: Score {score:.2f}")
    
    # Sort by score (highest first)
    scored_responses.sort(key=lambda x: x[1], reverse=True)
    best_response, best_score = scored_responses[0]
    
    print(f"🏆 Best response: {best_response.provider} (Score: {best_score:.2f})")
    
    try:
        confirmation_tx = ogpu.client.confirm_response(best_response.address)
        print(f"✅ Best response confirmed!")
        return best_response.data
    except Exception as e:
        print(f"❌ Confirmation failed: {e}")
        return None

def calculate_response_score(response_data: str) -> float:
    """Calculate quality score for response"""
    score = 0.0
    
    # Length score (normalized)
    length_score = min(len(response_data) / 1000, 1.0) * 0.3
    score += length_score
    
    # Content quality
    if not any(word in response_data.lower() for word in ["error", "failed", "timeout"]):
        score += 0.4
    
    # Structure score (has proper formatting)
    if len(response_data.split('\n')) > 1:
        score += 0.2
    
    # Completeness (ends properly)
    if response_data.strip().endswith(('.', '!', '?', '"')):
        score += 0.1
    
    return score
```

### Consensus-based Confirmation

```python
def confirm_by_consensus(task_address: str, min_consensus: int = 2):
    """Confirm response that appears most frequently (consensus)"""
    responses = ogpu.client.get_task_responses(task_address)
    
    submitted_responses = [r for r in responses if r.status == "submitted"]
    
    if len(submitted_responses) < min_consensus:
        print(f"❌ Need at least {min_consensus} responses for consensus")
        return None
    
    # Group similar responses
    response_groups = {}
    for response in submitted_responses:
        # Simple similarity check (you can improve this)
        key = response.data[:100]  # First 100 chars as similarity key
        
        if key not in response_groups:
            response_groups[key] = []
        response_groups[key].append(response)
    
    # Find group with most responses
    largest_group = max(response_groups.values(), key=len)
    
    if len(largest_group) >= min_consensus:
        consensus_response = largest_group[0]  # Take first from consensus group
        
        print(f"✅ Consensus found: {len(largest_group)} providers agree")
        
        try:
            confirmation_tx = ogpu.client.confirm_response(consensus_response.address)
            print(f"✅ Consensus response confirmed!")
            return consensus_response.data
        except Exception as e:
            print(f"❌ Confirmation failed: {e}")
    else:
        print(f"❌ No consensus reached (max agreement: {len(largest_group)})")
    
    return None
```

## 📊 Complete Confirmation Workflow

### Smart Confirmation Strategy

```python
def smart_confirm_response(task_address: str, strategy: str = "quality"):
    """Smart confirmation using different strategies"""
    
    strategies = {
        "first": auto_confirm_first_submitted,
        "quality": auto_confirm_with_validation, 
        "best": confirm_best_scored_response,
        "consensus": confirm_by_consensus,
        "manual": confirm_response_manually
    }
    
    if strategy not in strategies:
        print(f"❌ Unknown strategy: {strategy}")
        print(f"Available: {list(strategies.keys())}")
        return None
    
    print(f"🎯 Using {strategy} confirmation strategy")
    return strategies[strategy](task_address)

# Usage examples
result = smart_confirm_response(task_address, "quality")     # Auto with validation
result = smart_confirm_response(task_address, "manual")      # Manual review
result = smart_confirm_response(task_address, "consensus")   # Wait for agreement
```