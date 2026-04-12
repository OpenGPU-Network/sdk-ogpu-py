import os

from ogpu.client import ChainConfig, ChainId, set_agent

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

tx_hash = set_agent(
    agent_address="0xeBa8Cf76e6415A03D28f9D40c54440c894a67956",
    value=True,
    private_key=os.getenv("MASTER_PRIVATE_KEY"),
)

print(f"set_agent tx: {tx_hash}")
