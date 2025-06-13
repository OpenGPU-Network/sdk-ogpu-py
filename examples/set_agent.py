import os

from ogpu.agent import set_agent

qwe = set_agent(
    agent_address="0xeBa8Cf76e6415A03D28f9D40c54440c894a67956",  # Example address
    value=True,  # Set to True to enable the agent
    private_key=os.getenv(
        "MASTER_PRIVATE_KEY"
    ),  # Ensure this is set in your environment
)
