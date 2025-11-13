"""
Decentralized Identity (DID) Resolver for Mesh Networks

This module implements DID resolution and management for mesh network users
across multiple blockchain networks including Ethereum, Polygon, Solana, etc.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

try:
    import didkit
    _HAS_DIDKIT = True
except ImportError:
    _HAS_DIDKIT = False
    didkit = None

logger = logging.getLogger(__name__)


class DIDMethod(Enum):
    """Supported DID methods."""
    ETHR = "ethr"  # Ethereum
    KEY = "key"    # Key-based
    WEB = "web"    # Web-based
    SOL = "sol"    # Solana
    POLYGON = "polygon"  # Polygon
    BSC = "bsc"    # Binance Smart Chain
    AVAX = "avax"  # Avalanche


@dataclass
class DIDDocument:
    """DID Document structure."""
    id: str
    controller: Optional[str]
    also_known_as: List[str]
    verification_method: List[Dict[str, Any]]
    authentication: List[Union[str, Dict[str, Any]]]
    assertion_method: List[Union[str, Dict[str, Any]]]
    key_agreement: List[Union[str, Dict[str, Any]]]
    capability_invocation: List[Union[str, Dict[str, Any]]]
    capability_delegation: List[Union[str, Dict[str, Any]]]
    service: List[Dict[str, Any]]
    proof: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": self.id,
            "controller": self.controller,
            "alsoKnownAs": self.also_known_as,
            "verificationMethod": self.verification_method,
            "authentication": self.authentication,
            "assertionMethod": self.assertion_method,
            "keyAgreement": self.key_agreement,
            "capabilityInvocation": self.capability_invocation,
            "capabilityDelegation": self.capability_delegation,
            "service": self.service,
            "proof": self.proof
        }


@dataclass
class DIDResolutionResult:
    """Result of DID resolution."""
    did_document: Optional[DIDDocument]
    did_document_metadata: Dict[str, Any]
    did_resolution_metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "didDocument": self.did_document.to_dict() if self.did_document else None,
            "didDocumentMetadata": self.did_document_metadata,
            "didResolutionMetadata": self.did_resolution_metadata
        }


class DIDResolver:
    """
    Universal DID Resolver supporting multiple blockchain networks.

    Provides functionality to resolve, create, and manage DIDs across
    different blockchain ecosystems for mesh network identity management.
    """

    def __init__(self):
        self.resolvers: Dict[DIDMethod, Any] = {}
        self.cache: Dict[str, DIDResolutionResult] = {}
        self.cache_ttl = 300  # 5 minutes

        # Initialize resolvers for different methods
        self._initialize_resolvers()

    def _initialize_resolvers(self):
        """Initialize resolvers for different DID methods."""
        # Ethereum DID resolver
        try:
            from .resolvers import EthereumDIDResolver
            self.resolvers[DIDMethod.ETHR] = EthereumDIDResolver()
        except ImportError:
            logger.warning("Ethereum DID resolver not available")

        # Key-based DID resolver
        try:
            from .resolvers import KeyDIDResolver
            self.resolvers[DIDMethod.KEY] = KeyDIDResolver()
        except ImportError:
            logger.warning("Key DID resolver not available")

        # Web DID resolver
        try:
            from .resolvers import WebDIDResolver
            self.resolvers[DIDMethod.WEB] = WebDIDResolver()
        except ImportError:
            logger.warning("Web DID resolver not available")

    async def resolve(self, did: str, options: Dict[str, Any] = None) -> DIDResolutionResult:
        """
        Resolve a DID to its DID Document.

        Args:
            did: The DID to resolve
            options: Resolution options

        Returns:
            DIDResolutionResult containing the resolved document
        """
        # Check cache first
        if did in self.cache:
            cached_result = self.cache[did]
            # Check if cache is still valid
            if asyncio.get_event_loop().time() - cached_result.did_resolution_metadata.get('resolved_at', 0) < self.cache_ttl:
                return cached_result

        try:
            # Parse DID
            did_parts = did.split(':')
            if len(did_parts) < 3 or did_parts[0] != 'did':
                raise ValueError(f"Invalid DID format: {did}")

            method = DIDMethod(did_parts[1])

            # Get appropriate resolver
            if method not in self.resolvers:
                return DIDResolutionResult(
                    did_document=None,
                    did_document_metadata={},
                    did_resolution_metadata={
                        'error': 'methodNotSupported',
                        'message': f'DID method {method.value} not supported',
                        'resolved_at': asyncio.get_event_loop().time()
                    }
                )

            resolver = self.resolvers[method]

            # Resolve DID
            result = await resolver.resolve(did, options or {})

            # Cache result
            self.cache[did] = result

            return result

        except Exception as e:
            logger.error(f"DID resolution failed for {did}: {e}")
            return DIDResolutionResult(
                did_document=None,
                did_document_metadata={},
                did_resolution_metadata={
                    'error': 'resolutionFailed',
                    'message': str(e),
                    'resolved_at': asyncio.get_event_loop().time()
                }
            )

    async def create_did(self, method: DIDMethod, options: Dict[str, Any] = None) -> str:
        """
        Create a new DID.

        Args:
            method: The DID method to use
            options: Creation options

        Returns:
            The created DID
        """
        if method not in self.resolvers:
            raise ValueError(f"DID method {method.value} not supported")

        resolver = self.resolvers[method]
        return await resolver.create(options or {})

    async def update_did_document(self, did: str, updates: Dict[str, Any]) -> bool:
        """
        Update a DID Document.

        Args:
            did: The DID to update
            updates: Document updates

        Returns:
            True if update successful
        """
        try:
            # Parse DID method
            method = DIDMethod(did.split(':')[1])

            if method not in self.resolvers:
                raise ValueError(f"DID method {method.value} not supported")

            resolver = self.resolvers[method]
            success = await resolver.update_document(did, updates)

            if success:
                # Invalidate cache
                if did in self.cache:
                    del self.cache[did]

            return success

        except Exception as e:
            logger.error(f"DID document update failed for {did}: {e}")
            return False

    async def verify_credential(self, credential: Dict[str, Any]) -> bool:
        """
        Verify a Verifiable Credential.

        Args:
            credential: The credential to verify

        Returns:
            True if credential is valid
        """
        try:
            if not _HAS_DIDKIT:
                # Fallback verification without didkit
                return await self._verify_credential_fallback(credential)

            # Use didkit for verification
            credential_json = json.dumps(credential)
            result = didkit.verify_credential(credential_json, "{}")

            result_dict = json.loads(result)
            return result_dict.get('verified', False)

        except Exception as e:
            logger.error(f"Credential verification failed: {e}")
            return False

    async def _verify_credential_fallback(self, credential: Dict[str, Any]) -> bool:
        """Fallback credential verification without didkit."""
        try:
            # Basic validation
            if 'issuer' not in credential or 'proof' not in credential:
                return False

            issuer_did = credential['issuer']['id'] if isinstance(credential['issuer'], dict) else credential['issuer']

            # Resolve issuer DID
            issuer_result = await self.resolve(issuer_did)
            if not issuer_result.did_document:
                return False

            # TODO: Implement cryptographic verification
            # This would verify the proof against the issuer's public key

            return True

        except Exception as e:
            logger.error(f"Fallback credential verification failed: {e}")
            return False

    def get_supported_methods(self) -> List[str]:
        """Get list of supported DID methods."""
        return [method.value for method in self.resolvers.keys()]

    def clear_cache(self):
        """Clear the DID resolution cache."""
        self.cache.clear()


class MeshDIDManager:
    """
    DID Manager for Mesh Network Users.

    Manages DIDs for mesh network participants, integrating with
    voting systems and access control.
    """

    def __init__(self, resolver: DIDResolver):
        self.resolver = resolver
        self.user_dids: Dict[str, str] = {}  # user_id -> did
        self.did_users: Dict[str, str] = {}  # did -> user_id

    async def register_user_did(self, user_id: str, did: str) -> bool:
        """
        Register a DID for a mesh user.

        Args:
            user_id: Mesh user identifier
            did: User's DID

        Returns:
            True if registration successful
        """
        try:
            # Verify DID exists and is resolvable
            result = await self.resolver.resolve(did)
            if not result.did_document:
                logger.error(f"DID {did} could not be resolved")
                return False

            # Register mapping
            self.user_dids[user_id] = did
            self.did_users[did] = user_id

            logger.info(f"Registered DID {did} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register DID for user {user_id}: {e}")
            return False

    async def get_user_did(self, user_id: str) -> Optional[str]:
        """Get DID for a user."""
        return self.user_dids.get(user_id)

    async def get_did_user(self, did: str) -> Optional[str]:
        """Get user ID for a DID."""
        return self.did_users.get(did)

    async def verify_user_identity(self, user_id: str, challenge: str, signature: str) -> bool:
        """
        Verify user identity using DID.

        Args:
            user_id: User identifier
            challenge: Challenge string
            signature: Signature of challenge

        Returns:
            True if identity verified
        """
        try:
            did = self.user_dids.get(user_id)
            if not did:
                return False

            # Resolve DID document
            result = await self.resolver.resolve(did)
            if not result.did_document:
                return False

            # TODO: Implement signature verification using DID keys
            # This would verify the signature against the user's public key from DID document

            return True

        except Exception as e:
            logger.error(f"Identity verification failed for user {user_id}: {e}")
            return False

    async def create_mesh_credential(self, user_id: str, claims: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a Verifiable Credential for mesh network participation.

        Args:
            user_id: User identifier
            claims: Credential claims

        Returns:
            Verifiable Credential or None if failed
        """
        try:
            did = self.user_dids.get(user_id)
            if not did:
                return None

            credential = {
                "@context": ["https://www.w3.org/2018/credentials/v1"],
                "type": ["VerifiableCredential", "MeshNetworkCredential"],
                "issuer": did,
                "issuanceDate": asyncio.get_event_loop().time(),
                "credentialSubject": {
                    "id": did,
                    "meshUserId": user_id,
                    **claims
                }
            }

            # TODO: Add proof using DID key
            # This would sign the credential with the user's private key

            return credential

        except Exception as e:
            logger.error(f"Failed to create mesh credential for user {user_id}: {e}")
            return None
