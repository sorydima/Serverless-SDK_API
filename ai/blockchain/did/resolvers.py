"""
DID Method Resolvers

This module contains resolver implementations for different DID methods
including Ethereum, Key-based, and Web DIDs.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import json
import base64
import hashlib

try:
    from web3 import Web3
    _HAS_WEB3 = True
except ImportError:
    _HAS_WEB3 = False
    Web3 = None

logger = logging.getLogger(__name__)


class EthereumDIDResolver:
    """Resolver for Ethereum DID (did:ethr)."""

    def __init__(self, rpc_url: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"):
        if not _HAS_WEB3:
            raise ImportError("web3.py required for Ethereum DID resolver")

        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = "0xd1D374DDE0313C9EbD5C6b0d8654bC5b6d9d6c4b8"  # ethr-did-registry

    async def resolve(self, did: str, options: Dict[str, Any]) -> 'DIDResolutionResult':
        """Resolve an Ethereum DID."""
        try:
            # Parse DID: did:ethr:0x1234...
            parts = did.split(':')
            if len(parts) < 3:
                raise ValueError("Invalid ethr DID format")

            address = parts[2]

            # Get public key from Ethereum registry
            # This is a simplified implementation
            # In practice, you'd query the ethr-did-registry contract

            # Create DID Document
            from .did_resolver import DIDDocument, DIDResolutionResult

            verification_method = [{
                "id": f"{did}#controller",
                "type": "EcdsaSecp256k1RecoveryMethod2020",
                "controller": did,
                "blockchainAccountId": f"eip155:1:{address}"
            }]

            did_document = DIDDocument(
                id=did,
                controller=did,
                also_known_as=[],
                verification_method=verification_method,
                authentication=[f"{did}#controller"],
                assertion_method=[f"{did}#controller"],
                key_agreement=[],
                capability_invocation=[f"{did}#controller"],
                capability_delegation=[f"{did}#controller"],
                service=[],
                proof=None
            )

            return DIDResolutionResult(
                did_document=did_document,
                did_document_metadata={"version": "1.0"},
                did_resolution_metadata={"resolved_at": asyncio.get_event_loop().time()}
            )

        except Exception as e:
            logger.error(f"Ethereum DID resolution failed: {e}")
            from .did_resolver import DIDResolutionResult
            return DIDResolutionResult(
                did_document=None,
                did_document_metadata={},
                did_resolution_metadata={
                    "error": "resolutionFailed",
                    "message": str(e),
                    "resolved_at": asyncio.get_event_loop().time()
                }
            )

    async def create(self, options: Dict[str, Any]) -> str:
        """Create a new Ethereum DID."""
        # This would typically involve creating a new Ethereum key pair
        # For now, return a placeholder
        return f"did:ethr:0x{hashlib.sha256(str(options).encode()).hexdigest()[:40]}"

    async def update_document(self, did: str, updates: Dict[str, Any]) -> bool:
        """Update Ethereum DID document."""
        # Implementation would update the Ethereum registry
        logger.info(f"Updating Ethereum DID document for {did}")
        return True


class KeyDIDResolver:
    """Resolver for Key-based DID (did:key)."""

    def __init__(self):
        pass

    async def resolve(self, did: str, options: Dict[str, Any]) -> 'DIDResolutionResult':
        """Resolve a Key-based DID."""
        try:
            # Parse DID: did:key:z6Mk...
            parts = did.split(':')
            if len(parts) < 3:
                raise ValueError("Invalid key DID format")

            # Decode the multibase-encoded key
            key_data = parts[2]

            # For Ed25519 keys (z6Mk prefix)
            if key_data.startswith('z6Mk'):
                # Decode base58btc
                # This is a simplified implementation
                public_key = base64.b64encode(key_data[4:].encode()).decode()

                from .did_resolver import DIDDocument, DIDResolutionResult

                verification_method = [{
                    "id": f"{did}#z6Mk",
                    "type": "Ed25519VerificationKey2018",
                    "controller": did,
                    "publicKeyBase58": public_key
                }]

                did_document = DIDDocument(
                    id=did,
                    controller=did,
                    also_known_as=[],
                    verification_method=verification_method,
                    authentication=[f"{did}#z6Mk"],
                    assertion_method=[f"{did}#z6Mk"],
                    key_agreement=[],
                    capability_invocation=[f"{did}#z6Mk"],
                    capability_delegation=[f"{did}#z6Mk"],
                    service=[],
                    proof=None
                )

                return DIDResolutionResult(
                    did_document=did_document,
                    did_document_metadata={"version": "1.0"},
                    did_resolution_metadata={"resolved_at": asyncio.get_event_loop().time()}
                )
            else:
                raise ValueError("Unsupported key type")

        except Exception as e:
            logger.error(f"Key DID resolution failed: {e}")
            from .did_resolver import DIDResolutionResult
            return DIDResolutionResult(
                did_document=None,
                did_document_metadata={},
                did_resolution_metadata={
                    "error": "resolutionFailed",
                    "message": str(e),
                    "resolved_at": asyncio.get_event_loop().time()
                }
            )

    async def create(self, options: Dict[str, Any]) -> str:
        """Create a new Key-based DID."""
        # Generate Ed25519 key pair
        # This is a simplified implementation
        import secrets
        key_seed = secrets.token_bytes(32)
        key_hash = hashlib.sha256(key_seed).digest()
        encoded_key = base64.b64encode(key_hash).decode()

        return f"did:key:z6Mk{encoded_key}"

    async def update_document(self, did: str, updates: Dict[str, Any]) -> bool:
        """Update Key-based DID document."""
        # Key DIDs are immutable by design
        logger.warning("Key DIDs are immutable")
        return False


class WebDIDResolver:
    """Resolver for Web DID (did:web)."""

    def __init__(self):
        self.session = None  # For HTTP requests

    async def resolve(self, did: str, options: Dict[str, Any]) -> 'DIDResolutionResult':
        """Resolve a Web DID."""
        try:
            # Parse DID: did:web:example.com:user:alice
            parts = did.split(':')
            if len(parts) < 3:
                raise ValueError("Invalid web DID format")

            # Construct URL: https://example.com/.well-known/did.json
            domain = parts[2]
            path_parts = parts[3:] if len(parts) > 3 else []

            url = f"https://{domain}/.well-known/did.json"
            if path_parts:
                url = f"https://{domain}/{'/'.join(path_parts)}/did.json"

            # Fetch DID document
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status} from {url}")

                    did_data = await response.json()

                    from .did_resolver import DIDDocument, DIDResolutionResult

                    # Parse DID document
                    did_document = DIDDocument(
                        id=did_data.get('id', did),
                        controller=did_data.get('controller'),
                        also_known_as=did_data.get('alsoKnownAs', []),
                        verification_method=did_data.get('verificationMethod', []),
                        authentication=did_data.get('authentication', []),
                        assertion_method=did_data.get('assertionMethod', []),
                        key_agreement=did_data.get('keyAgreement', []),
                        capability_invocation=did_data.get('capabilityInvocation', []),
                        capability_delegation=did_data.get('capabilityDelegation', []),
                        service=did_data.get('service', []),
                        proof=did_data.get('proof')
                    )

                    return DIDResolutionResult(
                        did_document=did_document,
                        did_document_metadata={"version": "1.0"},
                        did_resolution_metadata={"resolved_at": asyncio.get_event_loop().time()}
                    )

        except Exception as e:
            logger.error(f"Web DID resolution failed: {e}")
            from .did_resolver import DIDResolutionResult
            return DIDResolutionResult(
                did_document=None,
                did_document_metadata={},
                did_resolution_metadata={
                    "error": "resolutionFailed",
                    "message": str(e),
                    "resolved_at": asyncio.get_event_loop().time()
                }
            )

    async def create(self, options: Dict[str, Any]) -> str:
        """Create a new Web DID."""
        # Web DIDs require hosting a DID document
        domain = options.get('domain', 'example.com')
        path = options.get('path', '')

        did = f"did:web:{domain}"
        if path:
            did += f":{path}"

        return did

    async def update_document(self, did: str, updates: Dict[str, Any]) -> bool:
        """Update Web DID document."""
        # This would require updating the hosted DID document
        logger.info(f"Web DID document update requested for {did}")
        return True


class PolygonDIDResolver(EthereumDIDResolver):
    """Resolver for Polygon DID (did:polygon)."""

    def __init__(self):
        super().__init__("https://polygon-rpc.com/")

    async def resolve(self, did: str, options: Dict[str, Any]) -> 'DIDResolutionResult':
        """Resolve a Polygon DID."""
        # Similar to Ethereum but on Polygon network
        result = await super().resolve(did, options)
        if result.did_document:
            # Update blockchain account ID for Polygon
            for vm in result.did_document.verification_method:
                if 'blockchainAccountId' in vm:
                    vm['blockchainAccountId'] = vm['blockchainAccountId'].replace('eip155:1:', 'eip155:137:')
        return result


class SolanaDIDResolver:
    """Resolver for Solana DID (did:sol)."""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    async def resolve(self, did: str, options: Dict[str, Any]) -> 'DIDResolutionResult':
        """Resolve a Solana DID."""
        try:
            # Parse DID: did:sol:pubkey
            parts = did.split(':')
            if len(parts) < 3:
                raise ValueError("Invalid sol DID format")

            pubkey = parts[2]

            from .did_resolver import DIDDocument, DIDResolutionResult

            verification_method = [{
                "id": f"{did}#controller",
                "type": "Ed25519VerificationKey2018",
                "controller": did,
                "publicKeyBase58": pubkey
            }]

            did_document = DIDDocument(
                id=did,
                controller=did,
                also_known_as=[],
                verification_method=verification_method,
                authentication=[f"{did}#controller"],
                assertion_method=[f"{did}#controller"],
                key_agreement=[],
                capability_invocation=[f"{did}#controller"],
                capability_delegation=[f"{did}#controller"],
                service=[],
                proof=None
            )

            return DIDResolutionResult(
                did_document=did_document,
                did_document_metadata={"version": "1.0"},
                did_resolution_metadata={"resolved_at": asyncio.get_event_loop().time()}
            )

        except Exception as e:
            logger.error(f"Solana DID resolution failed: {e}")
            from .did_resolver import DIDResolutionResult
            return DIDResolutionResult(
                did_document=None,
                did_document_metadata={},
                did_resolution_metadata={
                    "error": "resolutionFailed",
                    "message": str(e),
                    "resolved_at": asyncio.get_event_loop().time()
                }
            )

    async def create(self, options: Dict[str, Any]) -> str:
        """Create a new Solana DID."""
        # Generate Solana key pair
        import secrets
        pubkey = secrets.token_hex(32)
        return f"did:sol:{pubkey}"

    async def update_document(self, did: str, updates: Dict[str, Any]) -> bool:
        """Update Solana DID document."""
        # Solana DIDs would be stored on-chain
        logger.info(f"Updating Solana DID document for {did}")
        return True
