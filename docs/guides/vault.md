# Vault operations

The **Vault** contract holds staked tokens for providers, lets clients
escrow task payments, and handles unbonding and earnings claims. Vault
operations are **role-agnostic** — any account can hold a vault balance.

!!! warning "Signer is always required"
    Vault operations **never** fall back to an env var. Every write
    takes `signer=` as a keyword argument. This is intentional: it
    prevents accidentally depositing or withdrawing from the wrong
    account if multiple roles share the process.

## Deposit

`deposit(account, amount, *, signer)` — sends native tokens into the
vault on behalf of `account`. The signer pays gas; `account` receives
the credit.

```python
from web3 import Web3
from ogpu.protocol import vault

vault.deposit(
    "0xBENEFICIARY",
    amount=Web3.to_wei(1, "ether"),
    signer=MY_KEY,
)
```

Typically `signer` and `account` are the same address (you deposit for
yourself), but they don't have to be — a master can deposit on behalf
of a managed provider.

## Withdraw

`withdraw(amount, *, signer)` — pulls `amount` back out of the signer's
vault balance. Only works on the unlocked portion.

```python
vault.withdraw(Web3.to_wei(0.5, "ether"), signer=MY_KEY)
```

## Lock and unbond

Staking happens via `lock` and `unbond`. Locked tokens are what makes
a provider eligible to register to sources (`Vault.minLockupPerSource`
is checked on every `register` call).

```python
# Stake 1 OGPU
vault.lock(Web3.to_wei(1, "ether"), signer=PROVIDER_KEY)

# Start unbonding 0.5 OGPU — begins the cooldown
vault.unbond(Web3.to_wei(0.5, "ether"), signer=PROVIDER_KEY)

# Cancel the unbonding before it matures — funds stay locked
vault.cancel_unbonding(signer=PROVIDER_KEY)
```

Unbonded tokens are not immediately available for withdraw — they have
to wait out the unbonding period first.

```python
period = vault.get_unbonding_period()       # seconds
timestamp = vault.get_unbonding_timestamp("0xADDRESS")  # when it will mature
```

## Claim

After the unbonding period elapses, `claim` moves the unbonded amount
back into the liquid balance, where it can be withdrawn:

```python
vault.claim(signer=PROVIDER_KEY)
vault.withdraw(Web3.to_wei(0.5, "ether"), signer=PROVIDER_KEY)
```

## Reads

Every view function is exposed at the module level. All take an address
argument and hit the chain fresh.

| Function | Returns |
|---|---|
| `get_balance_of(addr)` | Available (liquid) balance in wei |
| `get_lockup_of(addr)` | Locked balance in wei |
| `get_unbonding_of(addr)` | Amount currently unbonding |
| `get_unbonding_timestamp(addr)` | Unix timestamp when unbonding matures |
| `get_total_earnings_of(addr)` | Cumulative earnings |
| `get_frozen_payment(addr)` | Payment escrowed against pending tasks |
| `get_sanction_of(addr)` | Sanction amount if any |
| `is_eligible(addr)` | `True` if the account can participate in tasks |
| `is_whitelisted(addr)` | `True` if explicitly whitelisted |
| `get_min_lockup_per_source()` | Minimum lockup required to register to a source |
| `get_unbonding_period()` | Unbonding cooldown in seconds |

```python
addr = "0xMY_ADDR"
print(f"Balance:  {vault.get_balance_of(addr)}")
print(f"Lockup:   {vault.get_lockup_of(addr)}")
print(f"Unbonding:{vault.get_unbonding_of(addr)}")
print(f"Eligible: {vault.is_eligible(addr)}")
```

## Full lifecycle example

```python
from web3 import Web3
from ogpu.protocol import vault

ADDR = "0xPROVIDER"
KEY = "0xPROVIDER_KEY"

# 1. Deposit 1 OGPU
vault.deposit(ADDR, Web3.to_wei(1, "ether"), signer=KEY)
assert vault.get_balance_of(ADDR) == 10**18

# 2. Lock 0.5 OGPU (now registerable to a source)
vault.lock(Web3.to_wei(0.5, "ether"), signer=KEY)
assert vault.get_lockup_of(ADDR) == 5 * 10**17

# 3. Later: start unbonding
vault.unbond(Web3.to_wei(0.3, "ether"), signer=KEY)
assert vault.get_unbonding_of(ADDR) == 3 * 10**17

# 4. Wait for the unbonding period to elapse
import time
time.sleep(vault.get_unbonding_period() + 5)

# 5. Claim — unbonded amount returns to the balance
vault.claim(signer=KEY)

# 6. Withdraw — pulls it out
vault.withdraw(Web3.to_wei(0.3, "ether"), signer=KEY)
```

## Convenience via Provider / Master instances

If you already hold a `Provider` or `Master` instance for a given
address, the synthetic classes expose convenience wrappers that
pre-fill the account argument:

```python
from ogpu.protocol import Provider

provider = Provider("0xPROV")
provider.stake(Web3.to_wei(1, "ether"), signer=KEY)       # → vault.lock
provider.unstake(Web3.to_wei(0.5, "ether"), signer=KEY)   # → vault.unbond
provider.claim_earnings(signer=KEY)                        # → vault.claim
provider.deposit_to_vault(Web3.to_wei(1, "ether"), signer=KEY)  # → vault.deposit(provider.address, ...)
```

These are one-line delegations to the module functions. Use whichever
you prefer.

## Errors

Vault operations raise typed errors from the `VaultError` domain:

```python
from ogpu.types import (
    InsufficientBalanceError,
    InsufficientLockupError,
    UnbondingPeriodNotElapsedError,
    NotEligibleError,
)

try:
    vault.lock(Web3.to_wei(5, "ether"), signer=KEY)
except InsufficientBalanceError as e:
    print(f"Not enough balance: need {e.required}, have {e.available}")
```

See [errors](errors.md) for the full `VaultError` subclasses.
