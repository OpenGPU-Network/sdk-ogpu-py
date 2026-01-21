# Nonce Management in OGPU SDK

## 🎯 Overview

Version 0.2.0.14 introduces comprehensive nonce management to prevent stuck transactions and nonce-related errors in the OGPU SDK.

## 🚀 Features

### 1. Automatic Retry with Error Detection

All transaction functions now automatically detect and recover from:
- **Nonce too low** errors
- **Replacement transaction underpriced** errors
- **Known transaction** errors

### 2. Manual Nonce Utilities

Four new utility functions for manual nonce management:

```python
from ogpu.client import (
    fix_nonce,              # Fix stuck nonce issues
    reset_nonce_cache,      # Reset SDK nonce cache
    clear_all_nonce_caches, # Clear all caches
    get_nonce_info,         # Get detailed nonce info
)
```

### 3. Manual Nonce Override

All transaction functions now support manual nonce override:

```python
# Override nonce manually (advanced use)
publish_task(task_info, nonce=42)
```

### 4. Thread-Safe Nonce Manager

Internal `NonceManager` class provides:
- Thread-safe nonce caching
- Automatic nonce incrementing
- Per-address lock management
- `pending` block identifier usage

---

## 📖 Usage Guide

### Basic Usage (Automatic)

The SDK now handles nonce errors automatically:

```python
from ogpu.client import publish_task, TaskInfo

# Just call the function - auto-retry is enabled by default
task_address = publish_task(task_info)
```

**What happens behind the scenes:**
1. Transaction fails with nonce error
2. SDK automatically calls `fix_nonce()`
3. Pending transactions are cancelled
4. Nonce cache is reset
5. Transaction is retried
6. Success! ✅

---

### Manual Nonce Fix

If you encounter nonce errors, use `fix_nonce()`:

```python
from ogpu.client import fix_nonce

# Fix all nonce issues for your account
fix_nonce()
```

**What it does:**
1. Detects pending transactions
2. Cancels them with higher gas price
3. Clears SDK nonce cache
4. Returns next available nonce

---

### Get Nonce Information

Check your current nonce status:

```python
from ogpu.client import get_nonce_info

info = get_nonce_info()
print(f"Mined nonce: {info['mined_nonce']}")
print(f"Pending nonce: {info['pending_nonce']}")
print(f"Has pending: {info['has_pending']}")
print(f"Pending count: {info['pending_count']}")
```

---

### Reset Nonce Cache

Clear the SDK's internal nonce cache:

```python
from ogpu.client import reset_nonce_cache

# Reset cache for current account
reset_nonce_cache()

# SDK will fetch fresh nonce from blockchain on next transaction
```

---

### Manual Nonce Override

For advanced users who need full control:

```python
from ogpu.client import publish_task, TaskInfo

# Specify exact nonce to use
task_address = publish_task(task_info, nonce=42)
```

⚠️ **Warning**: Only use manual override if you know what you're doing!

---

### Disable Auto-Fix

If you want to handle errors manually:

```python
from ogpu.client import publish_task, TaskInfo

try:
    task_address = publish_task(task_info, auto_fix_nonce=False)
except Exception as e:
    if "nonce" in str(e).lower():
        # Handle nonce error manually
        from ogpu.client import fix_nonce
        fix_nonce()
        # Retry
        task_address = publish_task(task_info)
```

---

## 🔧 Function Reference

### `fix_nonce(address=None, private_key=None) -> int`

Fix stuck nonce issues by cancelling pending transactions.

**Parameters:**
- `address` (str, optional): Address to fix. If None, derived from private_key.
- `private_key` (str, optional): Private key. If None, uses `CLIENT_PRIVATE_KEY` env var.

**Returns:**
- `int`: Next available nonce after fixing

**Example:**
```python
# Fix nonce for current account
next_nonce = fix_nonce()
print(f"Ready to send transaction with nonce: {next_nonce}")
```

---

### `get_nonce_info(address=None, private_key=None) -> dict`

Get detailed nonce information for an address.

**Parameters:**
- `address` (str, optional): Address to check. If None, derived from private_key.
- `private_key` (str, optional): Private key. If None, uses `CLIENT_PRIVATE_KEY` env var.

**Returns:**
- `dict`: Nonce information containing:
  - `address`: The address
  - `mined_nonce`: Number of mined transactions
  - `pending_nonce`: Number of mined + pending transactions
  - `cached_nonce`: SDK's cached nonce (None if not cached)
  - `has_pending`: Whether there are pending transactions
  - `pending_count`: Number of pending transactions

**Example:**
```python
info = get_nonce_info()
if info['has_pending']:
    print(f"Warning: {info['pending_count']} pending transactions!")
```

---

### `reset_nonce_cache(address=None, private_key=None) -> None`

Reset the SDK's internal nonce cache without cancelling transactions.

**Parameters:**
- `address` (str, optional): Address to reset. If None, derived from private_key.
- `private_key` (str, optional): Private key. If None, uses `CLIENT_PRIVATE_KEY` env var.

**Example:**
```python
# Force SDK to fetch fresh nonce on next transaction
reset_nonce_cache()
```

---

### `clear_all_nonce_caches() -> None`

Clear all nonce caches for all addresses.

**Example:**
```python
# Complete cache reset (useful for testing)
clear_all_nonce_caches()
```

---

## 🎓 Common Scenarios

### Scenario 1: Transaction Stuck for Hours

```python
from ogpu.client import fix_nonce, publish_task

# Your transaction is stuck
# Just call fix_nonce() and retry
fix_nonce()
task_address = publish_task(task_info)  # Will work now!
```

---

### Scenario 2: "Nonce Too Low" Error

```python
# Error: nonce too low

# Solution 1: Let SDK auto-fix (default behavior)
task_address = publish_task(task_info)  # Auto-retry enabled

# Solution 2: Manual fix
from ogpu.client import fix_nonce
fix_nonce()
task_address = publish_task(task_info)
```

---

### Scenario 3: "Replacement Transaction Underpriced"

```python
# Error: replacement transaction underpriced

# SDK will automatically:
# 1. Wait 5 seconds
# 2. Fetch fresh gas price
# 3. Retry transaction
# No action needed! Just wait.
```

---

### Scenario 4: Multiple Rapid Transactions

```python
from ogpu.client import publish_task

# Send multiple transactions rapidly
# SDK uses 'pending' block identifier to prevent nonce collisions
for i in range(5):
    task_address = publish_task(task_info)
    print(f"Task {i+1}: {task_address}")
```

---

### Scenario 5: Check Before Sending

```python
from ogpu.client import get_nonce_info, fix_nonce, publish_task

# Check nonce status first
info = get_nonce_info()

if info['has_pending']:
    print(f"Warning: {info['pending_count']} pending transactions")
    print("Fixing nonce before sending new transaction...")
    fix_nonce()

# Now safe to send
task_address = publish_task(task_info)
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# With command line argument
python test_nonce_management.py 0x1234567890abcdef...

# Or set environment variable
export CLIENT_PRIVATE_KEY=0x1234567890abcdef...
python test_nonce_management.py
```

**Tests included:**
1. ✅ Get nonce info
2. ✅ Nonce cache management
3. ✅ Clear all caches
4. ✅ Fix nonce (no pending TX)
5. ✅ Thread safety
6. ✅ Manual override simulation
7. ✅ Pending vs latest nonce

---

## ⚙️ Configuration

### Auto-Retry Settings

All transaction functions accept these parameters:

```python
publish_task(
    task_info,
    auto_fix_nonce=True,  # Enable/disable auto-fix
    max_retries=3,        # Maximum retry attempts
    nonce=None,           # Manual nonce override
)
```

**Default behavior:**
- `auto_fix_nonce=True`: Automatically retry on nonce errors
- `max_retries=3`: Try up to 3 times before giving up
- Uses `pending` block identifier by default

---

## 🔍 Under the Hood

### NonceManager Class

Internal class that manages nonces:

```python
# Automatic usage (you don't need to call these directly)
from ogpu.client.nonce_manager import NonceManager

# Get managed nonce
nonce = NonceManager.get_nonce(address, web3)

# Increment after successful transaction
NonceManager.increment_nonce(address, web3)

# Reset cache
NonceManager.reset_nonce(address, web3)
```

**Features:**
- Thread-safe operations (uses per-address locks)
- Uses `pending` block identifier
- Caches nonces to reduce RPC calls
- Automatically syncs with blockchain

---

## 📊 Error Detection

The SDK detects these error patterns:

### Nonce Errors
- `"nonce too low"`
- `"known transaction"`
- `"already known"`
- `"AlreadyKnown"`

**Action:** Auto-fix by calling `fix_nonce()` and retrying

### Gas Price Errors
- `"replacement transaction underpriced"`
- `"transaction underpriced"`

**Action:** Wait 5 seconds, reset cache, retry with fresh gas price

### Non-Recoverable Errors
- `"execution reverted"`
- `"insufficient funds"`
- Contract logic errors

**Action:** Immediately re-raise (no retry)

---

## 🎯 Best Practices

1. **Let SDK handle errors automatically** (default behavior)
   ```python
   # Just call the function - auto-retry enabled
   task_address = publish_task(task_info)
   ```

2. **Check nonce status before bulk operations**
   ```python
   info = get_nonce_info()
   if info['has_pending']:
       fix_nonce()
   ```

3. **Use `fix_nonce()` when stuck**
   ```python
   # If transactions are failing
   fix_nonce()
   # Then retry
   ```

4. **Avoid manual nonce override unless necessary**
   ```python
   # Only use if you have a specific reason
   publish_task(task_info, nonce=42)
   ```

5. **Reset cache after external changes**
   ```python
   # If you sent transactions outside SDK
   reset_nonce_cache()
   ```

---

## 🐛 Troubleshooting

### Problem: "Nonce too low" persists after fix

```python
# Solution: Force complete reset
from ogpu.client import clear_all_nonce_caches, fix_nonce

clear_all_nonce_caches()
fix_nonce()

# Now retry transaction
```

### Problem: Transaction stuck for >1 hour

```python
# Solution: Fix nonce (cancels stuck transactions)
from ogpu.client import fix_nonce

fix_nonce()
# Stuck transactions will be replaced with cancellation transactions
```

### Problem: "Replacement underpriced" won't go away

```python
# Solution: Wait longer between retries
import time
from ogpu.client import reset_nonce_cache, publish_task

reset_nonce_cache()
time.sleep(10)  # Wait for gas price to update
task_address = publish_task(task_info)
```

### Problem: Multiple failed retries

```python
# Solution: Check nonce info for diagnosis
from ogpu.client import get_nonce_info

info = get_nonce_info()
print(info)

# Check:
# - has_pending: Are there stuck transactions?
# - mined_nonce vs pending_nonce: What's the difference?
# - cached_nonce: Is cache out of sync?
```

---

## 📝 Migration Guide

### From v0.2.0.13 to v0.2.0.14

**No breaking changes!** All existing code continues to work.

**Before (v0.2.0.13):**
```python
# Manual error handling required
try:
    task_address = publish_task(task_info)
except Exception as e:
    if "nonce" in str(e):
        # Had to fix manually
        pass
```

**After (v0.2.0.14):**
```python
# Automatic error handling
task_address = publish_task(task_info)  # Just works! ✨
```

**New features available:**
```python
# Manual utilities if needed
from ogpu.client import fix_nonce, get_nonce_info

# Check status
info = get_nonce_info()

# Fix issues
fix_nonce()
```

---

## 🤝 Support

If you encounter issues:

1. **Check nonce status:**
   ```python
   from ogpu.client import get_nonce_info
   print(get_nonce_info())
   ```

2. **Try manual fix:**
   ```python
   from ogpu.client import fix_nonce
   fix_nonce()
   ```

3. **Run test suite:**
   ```bash
   python test_nonce_management.py <your_private_key>
   ```

4. **Report issues:**
   - GitHub: https://github.com/opengpu/sdk-ogpu-py/issues
   - Include: nonce info, error message, transaction hash

---

## 📄 License

MIT License - Same as OGPU SDK

---

## 🎉 Summary

Version 0.2.0.14 makes nonce management **completely automatic**:

- ✅ Auto-detect nonce errors
- ✅ Auto-fix with retry
- ✅ Thread-safe operations
- ✅ Manual utilities available
- ✅ No breaking changes
- ✅ Comprehensive testing

**Just upgrade and forget about nonce issues! 🚀**
