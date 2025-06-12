from web3 import Web3

from ogpu.client import (
    ChainConfig,
    ChainId,
    DeliveryMethod,
    ImageEnvironments,
    SourceInfo,
    publish_source,
)

ChainConfig.set_chain(ChainId.OGPU_TESTNET)

source_info = SourceInfo(
    name="test-source",
    description="test-description",
    logoUrl="https://www.dextools.io/resources/tokens/logos/ether/0x067def80d66fb69c276e53b641f37ff7525162f6.png",
    imageEnvs=ImageEnvironments(
        cpu="https://cipfs.ogpuscan.io/ipfs/QmNWFLL13ujf3KUTJvfNx42bA5fWDV96qqUdjY6nwpuwD9",
    ),
    minPayment=Web3.to_wei(0.01, "ether"),
    minAvailableLockup=Web3.to_wei(0, "ether"),
    maxExpiryDuration=86400,  # 24 hour in seconds
    deliveryMethod=DeliveryMethod.FIRST_RESPONSE,
)

# Publish the source
source_address = publish_source(source_info=source_info)

print(f"Source published at: {source_address}")
