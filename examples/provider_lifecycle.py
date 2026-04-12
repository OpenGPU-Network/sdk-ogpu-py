"""Provider lifecycle: master-provider pairing and source registration."""

from ogpu.client import ChainConfig, ChainId
from ogpu.protocol import Master, Provider

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

MASTER_KEY = "YOUR_MASTER_PRIVATE_KEY"
PROVIDER_KEY = "YOUR_PROVIDER_PRIVATE_KEY"
PROVIDER_ADDR = "0xPROVIDER_ADDRESS"
MASTER_ADDR = "0xMASTER_ADDRESS"
SOURCE_ADDR = "0xSOURCE_ADDRESS"

master = Master(MASTER_ADDR)
master.announce_provider(PROVIDER_ADDR, amount=0, signer=MASTER_KEY)
print(f"Master announced provider: {PROVIDER_ADDR}")

provider = Provider(PROVIDER_ADDR)
provider.announce_master(MASTER_ADDR, signer=PROVIDER_KEY)
print(f"Provider announced master: {provider.get_master()}")

provider.register_to(SOURCE_ADDR, env=1, signer=PROVIDER_KEY)
print("Provider registered to source")

print(f"Provider eligible: {provider.is_eligible()}")
print(f"Provider lockup: {provider.get_lockup()} wei")
