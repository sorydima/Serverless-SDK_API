"""
Deployment script for VoteValidator smart contract.

This script handles deployment to Ethereum and other EVM-compatible networks,
including contract verification and interaction utilities.
"""

import json
import os
from typing import Dict, Any, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import logging

logger = logging.getLogger(__name__)


class VoteValidatorDeployer:
    """Deployer for VoteValidator smart contract."""

    def __init__(self, rpc_url: str, private_key: str):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))

        # Add PoA middleware for networks like Polygon, BSC
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not self.web3.is_connected():
            raise ConnectionError(f"Cannot connect to {rpc_url}")

        self.account = Account.from_key(private_key)
        self.contract_address: Optional[str] = None

        # Load contract ABI and bytecode
        contract_path = os.path.join(os.path.dirname(__file__), 'vote_validator.json')
        if os.path.exists(contract_path):
            with open(contract_path, 'r') as f:
                contract_data = json.load(f)
                self.contract_abi = contract_data['abi']
                self.contract_bytecode = contract_data['bytecode']
        else:
            # Fallback: compile contract (requires solc)
            self.contract_abi, self.contract_bytecode = self._compile_contract()

    def _compile_contract(self) -> tuple:
        """Compile Solidity contract. Requires solc installation."""
        try:
            from solcx import compile_source

            contract_source = self._load_contract_source()
            compiled_sol = compile_source(contract_source, output_values=['abi', 'bin'])

            contract_interface = compiled_sol['<stdin>:VoteValidator']

            return contract_interface['abi'], contract_interface['bin']

        except ImportError:
            raise ImportError("solcx required for contract compilation. Install with: pip install py-solc-x")

    def _load_contract_source(self) -> str:
        """Load contract source code."""
        contract_file = os.path.join(os.path.dirname(__file__), 'vote_validator.sol')
        with open(contract_file, 'r') as f:
            return f.read()

    def deploy_contract(self, gas_price: Optional[int] = None) -> str:
        """Deploy the VoteValidator contract."""
        logger.info("Deploying VoteValidator contract...")

        # Build transaction
        transaction = {
            'from': self.account.address,
            'data': self.contract_bytecode,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 3000000,  # Adjust based on network
        }

        if gas_price:
            transaction['gasPrice'] = gas_price
        else:
            transaction['gasPrice'] = self.web3.eth.gas_price

        # Estimate gas
        try:
            estimated_gas = self.web3.eth.estimate_gas(transaction)
            transaction['gas'] = int(estimated_gas * 1.2)  # Add 20% buffer
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}")

        # Sign and send transaction
        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        logger.info(f"Deployment transaction sent: {tx_hash.hex()}")

        # Wait for transaction receipt
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt.status == 1:
            self.contract_address = tx_receipt.contractAddress
            logger.info(f"Contract deployed at: {self.contract_address}")
            return self.contract_address
        else:
            raise RuntimeError("Contract deployment failed")

    def get_contract(self):
        """Get contract instance."""
        if not self.contract_address:
            raise ValueError("Contract not deployed yet")

        return self.web3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )

    def create_session(self, title: str, options: list, duration_minutes: int,
                      min_participants: int, consensus_threshold: int) -> str:
        """Create a new voting session."""
        contract = self.get_contract()

        # Convert options to bytes32
        options_bytes32 = [Web3.keccak(text=opt) for opt in options]

        # Build transaction
        transaction = contract.functions.createSession(
            title,
            options_bytes32,
            duration_minutes,
            min_participants,
            consensus_threshold
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 500000,
            'gasPrice': self.web3.eth.gas_price
        })

        # Sign and send
        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for receipt
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        if tx_receipt.status == 1:
            # Extract session ID from logs
            logs = contract.events.SessionCreated().process_receipt(tx_receipt)
            if logs:
                return logs[0]['args']['sessionId'].hex()
            else:
                # Fallback: calculate session ID
                return Web3.keccak(text=f"{self.account.address}{title}{tx_receipt.blockNumber}").hex()
        else:
            raise RuntimeError("Session creation failed")

    def cast_vote(self, session_id: str, option_text: str) -> bool:
        """Cast a vote in a session."""
        contract = self.get_contract()

        option_id = Web3.keccak(text=option_text)

        # Build transaction
        transaction = contract.functions.castOnChainVote(
            session_id,
            option_id
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 300000,
            'gasPrice': self.web3.eth.gas_price
        })

        # Sign and send
        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)

        # Wait for receipt
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt.status == 1

    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get voting session results."""
        contract = self.get_contract()

        try:
            result = contract.functions.getSessionResults(session_id).call()

            return {
                'status': result[0],
                'options': [opt.hex() for opt in result[1]],
                'vote_counts': result[2],
                'total_votes': result[3],
                'finalized': result[4]
            }
        except Exception as e:
            logger.error(f"Failed to get session results: {e}")
            return {}

    def add_validator(self, validator_address: str) -> bool:
        """Add an authorized validator."""
        contract = self.get_contract()

        transaction = contract.functions.addValidator(validator_address).build_transaction({
            'from': self.account.address,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'gasPrice': self.web3.eth.gas_price
        })

        signed_txn = self.web3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt.status == 1


def deploy_to_network(network_config: Dict[str, str]) -> VoteValidatorDeployer:
    """
    Deploy contract to a specific network.

    Args:
        network_config: Dict with 'rpc_url' and 'private_key'
    """
    deployer = VoteValidatorDeployer(
        network_config['rpc_url'],
        network_config['private_key']
    )

    contract_address = deployer.deploy_contract()
    logger.info(f"VoteValidator deployed to {network_config.get('name', 'network')}: {contract_address}")

    return deployer


# Example usage
if __name__ == "__main__":
    # Configuration for different networks
    networks = {
        'ethereum': {
            'name': 'Ethereum Mainnet',
            'rpc_url': 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
            'private_key': 'YOUR_PRIVATE_KEY'
        },
        'polygon': {
            'name': 'Polygon',
            'rpc_url': 'https://polygon-rpc.com/',
            'private_key': 'YOUR_PRIVATE_KEY'
        },
        'bsc': {
            'name': 'Binance Smart Chain',
            'rpc_url': 'https://bsc-dataseed.binance.org/',
            'private_key': 'YOUR_PRIVATE_KEY'
        }
    }

    # Deploy to Polygon (example)
    try:
        deployer = deploy_to_network(networks['polygon'])

        # Create a test session
        session_id = deployer.create_session(
            title="Test Mesh Vote",
            options=["Option A", "Option B", "Option C"],
            duration_minutes=60,
            min_participants=3,
            consensus_threshold=60
        )

        print(f"Created voting session: {session_id}")

    except Exception as e:
        print(f"Deployment failed: {e}")
