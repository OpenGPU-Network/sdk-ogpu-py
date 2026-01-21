# Nonce Management

!!! info "New in v0.2.0.14"
    Comprehensive nonce management features were introduced in version 0.2.0.14 to prevent stuck transactions and provide automatic error recovery.

## Overview

Nonce management is critical for Ethereum transactions. A nonce is a sequential number that ensures transactions are processed in order. When nonces get out of sync or transactions get stuck, subsequent transactions will fail.

The OGPU SDK now provides **automatic nonce management** with:

- ✅ Automatic error detection and retry
- ✅ Thread-safe nonce caching
- ✅ Stuck transaction recovery
- ✅ Manual override capabilities

## Automatic Features (Default Behavior)

### Auto-Retry on Errors

All transaction functions automatically detect and recover from common nonce errors:

```python
from ogpu.client import publish_task, TaskInfo

# Just call the function - auto-retry is enabled by default
task_address = publish_task(task_info)
```

**What happens behind the scenes:**

1. Transaction fails with "nonce too low" error
2. SDK automatically calls `fix_nonce()`
3. Pending transactions are cancelled
4. Nonce cache is reset
5. Transaction is retried
6. Success! ✅

### Supported Error Types

The SDK automatically handles:

| Error Type | Description | Action |
|------------|-------------|--------|
| `nonce too low` | Nonce already used | Auto-fix and retry |
| `known transaction` | Duplicate transaction | Auto-fix and retry |
| `replacement transaction underpriced` | Gas price too low | Wait and retry |

## Manual Utilities

### Check Nonce Status

Get detailed information about your account's nonce state:

```python
from ogpu.client import get_nonce_info

info = get_nonce_info()
print(f"Mined transactions: {info['mined_nonce']}")
print(f"Pending transactions: {info['pending_count']}")

if info['has_pending']:
    print(f"⚠️  Warning: {info['pending_count']} stuck transaction(s)")
```

**Response:**

```python
{
    'address': '0x...',
    'mined_nonce': 42,           # Confirmed transactions
    'pending_nonce': 44,         # Confirmed + pending
    'cached_nonce': 44,          # SDK cache
    'has_pending': True,         # Has pending transactions?
    'pending_count': 2,          # Number of pending
}
```

### Fix Stuck Transactions

If transactions are stuck, manually trigger the fix:

```python
from ogpu.client import fix_nonce

# Fix all stuck transactions
next_nonce = fix_nonce()
print(f"Ready! Next nonce: {next_nonce}")
```

**What `fix_nonce()` does:**

1. Detects pending (stuck) transactions
2. Sends cancellation transactions (0 ETH to self with higher gas)
3. Clears SDK internal cache
4. Returns next available nonce

### Reset Nonce Cache

Clear the SDK's internal cache without canceling transactions:

```python
from ogpu.client import reset_nonce_cache

# Clear cache for current account
reset_nonce_cache()

# SDK will fetch fresh nonce on next transaction
```

### Clear All Caches

Reset everything (useful for testing):

```python
from ogpu.client import clear_all_nonce_caches

clear_all_nonce_caches()
```

## Advanced Usage

### Manual Nonce Override

For advanced users who need full control:

```python
from ogpu.client import publish_task

# Specify exact nonce
task_address = publish_task(task_info, nonce=42)
```

!!! warning "Use with Caution"
    Manual nonce override bypasses SDK management. Only use if you know what you're doing!

### Disable Auto-Fix

If you want to handle errors manually:

```python
from ogpu.client import publish_task, fix_nonce

try:
    # Disable auto-fix
    task_address = publish_task(task_info, auto_fix_nonce=False)
except Exception as e:
    if "nonce" in str(e).lower():
        # Handle manually
        fix_nonce()
        # Retry
        task_address = publish_task(task_info)
```

### Custom Retry Settings

Control retry behavior:

```python
from ogpu.client import publish_task

task_address = publish_task(
    task_info,
    auto_fix_nonce=True,   # Enable auto-fix (default)
    max_retries=5,         # Try up to 5 times (default: 3)
)
```

## Common Scenarios

### Scenario 1: Transaction Stuck for Hours

**Problem:** Your transaction is stuck in the mempool with low gas price.

**Solution:**

```python
from ogpu.client import fix_nonce, publish_task

# Fix stuck transactions
fix_nonce()

# Now send new transaction
task_address = publish_task(task_info)
```

### Scenario 2: "Nonce Too Low" Error

**Problem:** Getting "nonce too low" error when sending transactions.

**Solution 1 (Automatic):**

```python
# Just call the function - auto-retry handles it
task_address = publish_task(task_info)
```

**Solution 2 (Manual):**

```python
from ogpu.client import fix_nonce, publish_task

# Manually fix
fix_nonce()

# Then retry
task_address = publish_task(task_info)
```

### Scenario 3: Multiple Rapid Transactions

**Problem:** Need to send many transactions quickly without nonce collisions.

**Solution:**

```python
from ogpu.client import publish_task

# SDK uses 'pending' block identifier and caching
# No nonce collisions!
for i in range(100):
    task_address = publish_task(task_info)
    print(f"Task {i+1}: {task_address}")
```

### Scenario 4: Check Before Sending

**Problem:** Want to verify nonce status before sending important transactions.

**Solution:**

```python
from ogpu.client import get_nonce_info, fix_nonce, publish_task

# Check status first
info = get_nonce_info()

if info['has_pending']:
    print(f"⚠️  {info['pending_count']} pending transactions detected")
    print("Fixing before sending...")
    fix_nonce()

# Now safe to send
task_address = publish_task(task_info)
```

## All Transaction Functions

Nonce management is available in all transaction functions:

### Client Functions

```python
from ogpu.client import (
    publish_task,
    publish_source,
    confirm_response,
)

# All support: nonce, auto_fix_nonce, max_retries
task_address = publish_task(task_info, auto_fix_nonce=True)
source_address = publish_source(source_info, auto_fix_nonce=True)
tx_hash = confirm_response(response_addr, auto_fix_nonce=True)
```

### Agent Functions

```python
from ogpu.agent import set_agent

# Also supports nonce management
tx_hash = set_agent(
    agent_address,
    True,
    private_key,
    auto_fix_nonce=True
)
```

## API Reference

### `fix_nonce(address=None, private_key=None) -> int`

Fix stuck nonce issues by canceling pending transactions.

**Parameters:**

- `address` (str, optional): Address to fix. If None, derived from private_key.
- `private_key` (str, optional): Private key. If None, uses `CLIENT_PRIVATE_KEY` env var.

**Returns:**

- `int`: Next available nonce after fixing

**Example:**

```python
next_nonce = fix_nonce()
print(f"Ready with nonce: {next_nonce}")
```

---

### `get_nonce_info(address=None, private_key=None) -> dict`

Get detailed nonce information.

**Parameters:**

- `address` (str, optional): Address to check.
- `private_key` (str, optional): Private key to derive address from.

**Returns:**

- `dict`: Nonce information with keys:
    - `address`: The address
    - `mined_nonce`: Confirmed transactions
    - `pending_nonce`: Confirmed + pending
    - `cached_nonce`: SDK cache (or None)
    - `has_pending`: Boolean
    - `pending_count`: Number of pending

**Example:**

```python
info = get_nonce_info()
if info['has_pending']:
    print(f"Stuck: {info['pending_count']}")
```

---

### `reset_nonce_cache(address=None, private_key=None) -> None`

Reset SDK nonce cache.

**Parameters:**

- `address` (str, optional): Address to reset.
- `private_key` (str, optional): Private key to derive address from.

**Example:**

```python
reset_nonce_cache()
# Next transaction fetches fresh nonce
```

---

### `clear_all_nonce_caches() -> None`

Clear all nonce caches for all addresses.

**Example:**

```python
clear_all_nonce_caches()
```

## Best Practices

### 1. Let SDK Handle Errors Automatically

The default behavior is best for most use cases:

```python
# ✅ Good - automatic error handling
task_address = publish_task(task_info)
```

### 2. Check Status Before Bulk Operations

Verify nonce state before sending many transactions:

```python
# ✅ Good practice
info = get_nonce_info()
if info['has_pending']:
    fix_nonce()

# Now safe for bulk operations
for task_info in task_list:
    publish_task(task_info)
```

### 3. Use Manual Fix When Needed

If auto-retry fails, use manual fix:

```python
# ✅ Good - manual recovery
try:
    task_address = publish_task(task_info)
except Exception as e:
    if "nonce" in str(e).lower():
        fix_nonce()
        task_address = publish_task(task_info)
```

### 4. Avoid Unnecessary Manual Override

Only override nonce if you have a specific reason:

```python
# ❌ Bad - unnecessary manual control
task_address = publish_task(task_info, nonce=42)

# ✅ Good - let SDK manage
task_address = publish_task(task_info)
```

### 5. Reset Cache After External Changes

If you sent transactions outside the SDK:

```python
# ✅ Good - reset after external changes
# (sent transaction via MetaMask, another script, etc.)
reset_nonce_cache()

# Now SDK cache is synced
task_address = publish_task(task_info)
```

## Troubleshooting

### Problem: "Nonce too low" persists

**Solution:**

```python
from ogpu.client import clear_all_nonce_caches, fix_nonce

# Complete reset
clear_all_nonce_caches()
fix_nonce()

# Retry
task_address = publish_task(task_info)
```

### Problem: Transaction stuck for >1 hour

**Solution:**

```python
from ogpu.client import fix_nonce

# Cancel stuck transactions
fix_nonce()
# They'll be replaced with higher gas
```

### Problem: Multiple failed retries

**Solution:**

```python
from ogpu.client import get_nonce_info

# Diagnose the issue
info = get_nonce_info()
print(info)

# Check:
# - has_pending: Stuck transactions?
# - pending_count: How many?
# - cached_nonce: Cache out of sync?
```

### Problem: "Replacement underpriced"

**Solution:**

```python
import time
from ogpu.client import reset_nonce_cache, publish_task

# Wait for gas prices to update
reset_nonce_cache()
time.sleep(10)

# Retry
task_address = publish_task(task_info)
```

## Thread Safety

The SDK's nonce management is thread-safe:

```python
import threading
from ogpu.client import publish_task

def send_transaction(task_info):
    task_address = publish_task(task_info)
    print(f"Task: {task_address}")

# Safe to run concurrently
threads = []
for i in range(5):
    t = threading.Thread(target=send_transaction, args=(task_info,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

**Features:**

- Per-address locks prevent race conditions
- Nonces are sequential even with concurrent calls
- Thread-safe cache operations

## Testing

Test your nonce management setup:

```bash
# Run test suite
python test_nonce_management.py <private_key>
```

**Tests included:**

1. ✅ Get nonce info
2. ✅ Cache management
3. ✅ Fix nonce functionality
4. ✅ Thread safety
5. ✅ Manual override
6. ✅ Pending vs latest nonce

## Migration from v0.2.0.13

!!! success "No Breaking Changes"
    All existing code continues to work without modifications!

**Before (v0.2.0.13):**

```python
# Manual error handling required
try:
    task_address = publish_task(task_info)
except Exception as e:
    if "nonce" in str(e):
        # Had to handle manually
        pass
```

**After (v0.2.0.14):**

```python
# Automatic error handling
task_address = publish_task(task_info)  # Just works! ✨
```

**New features available:**

```python
# Manual utilities
from ogpu.client import fix_nonce, get_nonce_info

# Check status
info = get_nonce_info()

# Fix issues
fix_nonce()
```

## Under the Hood

### NonceManager Class

Internal class managing nonces (you don't need to use this directly):

**Features:**

- Thread-safe operations with per-address locks
- Uses `pending` block identifier (includes pending transactions)
- Caches nonces to reduce RPC calls
- Automatically syncs with blockchain

**Methods:**

```python
from ogpu.client.nonce_manager import NonceManager

# Get managed nonce (automatic)
nonce = NonceManager.get_nonce(address, web3)

# Increment after success (automatic)
NonceManager.increment_nonce(address, web3)

# Reset cache
NonceManager.reset_nonce(address, web3)
```

## Summary

Nonce management in v0.2.0.14:

- ✅ **Automatic** - Detects and fixes errors
- ✅ **Manual utilities** - For when you need control
- ✅ **Thread-safe** - Concurrent operations supported
- ✅ **Backward compatible** - No code changes needed
- ✅ **Well-tested** - Comprehensive test suite
- ✅ **Easy to use** - Just call the function!

**Forget about nonce issues and focus on building! 🚀**
