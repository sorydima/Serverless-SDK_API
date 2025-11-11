# Polkadot Bridge

## Overview
This module provides integration with the Polkadot blockchain network, enabling cross-chain communication and smart contract interactions.

## Features
- Connect to Polkadot and Kusama networks
- Submit extrinsics and query chain state
- Event monitoring and subscription
- Cross-chain message passing (XCMP)
- Support for Substrate-based chains

## Prerequisites
- Rust 1.65.0+
- Substrate development environment
- Polkadot.js API
- Web3 Foundation account (for on-chain operations)

## Installation
```bash
cargo add polkadot-runtime-common
cargo add substrate-subxt
```

## Usage
```rust
use sp_core::sr25519;
use subxt::{OnlineClient, PolkadotConfig};

#[subxt::subxt(runtime_metadata_path = "metadata.scale")]
pub mod polkadot {}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let api = OnlineClient::<PolkadotConfig>::from_url("wss://rpc.polkadot.io").await?;
    // Your code here
    Ok(())
}
```

## Configuration
Create a `config.toml` in the project root:
```toml
[polkadot]
endpoint = "wss://rpc.polkadot.io"
account_uri = "//Alice"  # Development account

[contracts]
gas_limit = 1000000000
storage_deposit_limit = 1000000000
```

## Testing
```bash
cargo test --features=test
```

## Security Considerations
- Use secure key management
- Validate all on-chain data
- Implement proper error handling
- Follow Polkadot security best practices

## License
See main LICENSE file.
