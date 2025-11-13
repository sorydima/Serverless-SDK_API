"""
Web5 Data Vault for Secure Local Storage

This module implements a secure data vault for storing mesh network user data
locally with encryption, access control, and decentralized synchronization.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import hashlib
import base64

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False
    Fernet = None
    PBKDF2HMAC = None

logger = logging.getLogger(__name__)


@dataclass
class VaultEntry:
    """Represents a data entry in the vault."""
    id: str
    data_type: str
    encrypted_data: str
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float
    access_control: Dict[str, Any]
    version: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'data_type': self.data_type,
            'encrypted_data': self.encrypted_data,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'access_control': self.access_control,
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VaultEntry':
        return cls(
            id=data['id'],
            data_type=data['data_type'],
            encrypted_data=data['encrypted_data'],
            metadata=data.get('metadata', {}),
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            access_control=data.get('access_control', {}),
            version=data.get('version', 1)
        )


@dataclass
class AccessPolicy:
    """Access control policy for vault entries."""
    policy_id: str
    owner_did: str
    allowed_dids: List[str]
    permissions: List[str]  # 'read', 'write', 'delete', 'share'
    conditions: Dict[str, Any]  # Time-based, location-based conditions
    expires_at: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_id': self.policy_id,
            'owner_did': self.owner_did,
            'allowed_dids': self.allowed_dids,
            'permissions': self.permissions,
            'conditions': self.conditions,
            'expires_at': self.expires_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccessPolicy':
        return cls(
            policy_id=data['policy_id'],
            owner_did=data['owner_did'],
            allowed_dids=data.get('allowed_dids', []),
            permissions=data.get('permissions', []),
            conditions=data.get('conditions', {}),
            expires_at=data.get('expires_at')
        )


class Web5DataVault:
    """
    Secure Data Vault for Web5-compatible local storage.

    Provides encrypted storage with access control, versioning, and
    decentralized synchronization capabilities for mesh network data.
    """

    def __init__(self, vault_path: str, password: str):
        if not _HAS_CRYPTOGRAPHY:
            raise ImportError("cryptography library required for data vault")

        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # Derive encryption key from password
        self.encryption_key = self._derive_key(password)

        # Vault storage
        self.entries: Dict[str, VaultEntry] = {}
        self.access_policies: Dict[str, AccessPolicy] = {}

        # Load existing vault data
        self._load_vault()

    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password."""
        salt = b'web5_vault_salt_2024'  # In production, use unique salt per vault
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using Fernet."""
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_data.encode()).decode()

    def _load_vault(self):
        """Load vault data from disk."""
        try:
            entries_file = self.vault_path / 'entries.json'
            policies_file = self.vault_path / 'policies.json'

            if entries_file.exists():
                with open(entries_file, 'r') as f:
                    entries_data = json.load(f)
                    for entry_data in entries_data.values():
                        entry = VaultEntry.from_dict(entry_data)
                        self.entries[entry.id] = entry

            if policies_file.exists():
                with open(policies_file, 'r') as f:
                    policies_data = json.load(f)
                    for policy_data in policies_data.values():
                        policy = AccessPolicy.from_dict(policy_data)
                        self.access_policies[policy.policy_id] = policy

            logger.info(f"Loaded vault with {len(self.entries)} entries and {len(self.access_policies)} policies")

        except Exception as e:
            logger.error(f"Failed to load vault: {e}")

    def _save_vault(self):
        """Save vault data to disk."""
        try:
            entries_file = self.vault_path / 'entries.json'
            policies_file = self.vault_path / 'policies.json'

            # Save entries
            entries_data = {eid: entry.to_dict() for eid, entry in self.entries.items()}
            with open(entries_file, 'w') as f:
                json.dump(entries_data, f, indent=2)

            # Save policies
            policies_data = {pid: policy.to_dict() for pid, policy in self.access_policies.items()}
            with open(policies_file, 'w') as f:
                json.dump(policies_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save vault: {e}")

    async def store_data(self, data_type: str, data: Union[str, Dict, List],
                        metadata: Dict[str, Any] = None, owner_did: str = None) -> str:
        """
        Store data in the vault.

        Args:
            data_type: Type of data (e.g., 'profile', 'credentials', 'mesh_config')
            data: Data to store
            metadata: Additional metadata
            owner_did: Owner's DID for access control

        Returns:
            Entry ID
        """
        try:
            # Generate entry ID
            entry_id = hashlib.sha256(f"{data_type}_{datetime.now().timestamp()}".encode()).hexdigest()

            # Serialize data
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data)
            else:
                data_str = str(data)

            # Encrypt data
            encrypted_data = self._encrypt_data(data_str)

            # Create entry
            entry = VaultEntry(
                id=entry_id,
                data_type=data_type,
                encrypted_data=encrypted_data,
                metadata=metadata or {},
                created_at=datetime.now().timestamp(),
                updated_at=datetime.now().timestamp(),
                access_control={'owner': owner_did} if owner_did else {},
                version=1
            )

            self.entries[entry_id] = entry
            self._save_vault()

            logger.info(f"Stored {data_type} data with ID {entry_id}")
            return entry_id

        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            raise

    async def retrieve_data(self, entry_id: str, requester_did: str = None) -> Optional[Union[str, Dict, List]]:
        """
        Retrieve data from the vault.

        Args:
            entry_id: Entry ID to retrieve
            requester_did: DID of the requester for access control

        Returns:
            Decrypted data or None if not found/access denied
        """
        try:
            if entry_id not in self.entries:
                return None

            entry = self.entries[entry_id]

            # Check access control
            if not await self._check_access(entry, requester_did):
                logger.warning(f"Access denied for entry {entry_id} to {requester_did}")
                return None

            # Decrypt data
            decrypted_data = self._decrypt_data(entry.encrypted_data)

            # Parse JSON if possible
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data

        except Exception as e:
            logger.error(f"Failed to retrieve data {entry_id}: {e}")
            return None

    async def update_data(self, entry_id: str, new_data: Union[str, Dict, List],
                         requester_did: str = None) -> bool:
        """
        Update data in the vault.

        Args:
            entry_id: Entry ID to update
            new_data: New data
            requester_did: DID of the requester

        Returns:
            True if update successful
        """
        try:
            if entry_id not in self.entries:
                return False

            entry = self.entries[entry_id]

            # Check write access
            if not await self._check_access(entry, requester_did, 'write'):
                return False

            # Serialize and encrypt new data
            if isinstance(new_data, (dict, list)):
                data_str = json.dumps(new_data)
            else:
                data_str = str(new_data)

            entry.encrypted_data = self._encrypt_data(data_str)
            entry.updated_at = datetime.now().timestamp()
            entry.version += 1

            self._save_vault()

            logger.info(f"Updated entry {entry_id} to version {entry.version}")
            return True

        except Exception as e:
            logger.error(f"Failed to update data {entry_id}: {e}")
            return False

    async def delete_data(self, entry_id: str, requester_did: str = None) -> bool:
        """
        Delete data from the vault.

        Args:
            entry_id: Entry ID to delete
            requester_did: DID of the requester

        Returns:
            True if deletion successful
        """
        try:
            if entry_id not in self.entries:
                return False

            entry = self.entries[entry_id]

            # Check delete access
            if not await self._check_access(entry, requester_did, 'delete'):
                return False

            del self.entries[entry_id]
            self._save_vault()

            logger.info(f"Deleted entry {entry_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete data {entry_id}: {e}")
            return False

    async def _check_access(self, entry: VaultEntry, requester_did: str = None,
                           permission: str = 'read') -> bool:
        """
        Check if requester has access to entry.

        Args:
            entry: Vault entry
            requester_did: Requester's DID
            permission: Permission to check

        Returns:
            True if access granted
        """
        # If no access control, allow access
        if not entry.access_control:
            return True

        # Owner always has access
        owner = entry.access_control.get('owner')
        if owner and owner == requester_did:
            return True

        # Check policies
        for policy in self.access_policies.values():
            if (requester_did in policy.allowed_dids and
                permission in policy.permissions):

                # Check expiration
                if policy.expires_at and datetime.now().timestamp() > policy.expires_at:
                    continue

                # Check conditions (simplified)
                # In production, implement time/location-based checks
                return True

        return False

    async def create_access_policy(self, owner_did: str, allowed_dids: List[str],
                                  permissions: List[str], conditions: Dict[str, Any] = None,
                                  expires_at: float = None) -> str:
        """
        Create an access policy.

        Args:
            owner_did: Policy owner's DID
            allowed_dids: List of allowed DIDs
            permissions: List of permissions
            conditions: Access conditions
            expires_at: Expiration timestamp

        Returns:
            Policy ID
        """
        policy_id = hashlib.sha256(f"policy_{owner_did}_{datetime.now().timestamp()}".encode()).hexdigest()

        policy = AccessPolicy(
            policy_id=policy_id,
            owner_did=owner_did,
            allowed_dids=allowed_dids,
            permissions=permissions,
            conditions=conditions or {},
            expires_at=expires_at
        )

        self.access_policies[policy_id] = policy
        self._save_vault()

        logger.info(f"Created access policy {policy_id}")
        return policy_id

    async def share_data(self, entry_id: str, target_did: str, permissions: List[str],
                        sharer_did: str = None) -> bool:
        """
        Share data with another DID.

        Args:
            entry_id: Entry to share
            target_did: Target DID
            permissions: Permissions to grant
            sharer_did: DID of the sharer

        Returns:
            True if sharing successful
        """
        try:
            if entry_id not in self.entries:
                return False

            entry = self.entries[entry_id]

            # Check if sharer has share permission
            if not await self._check_access(entry, sharer_did, 'share'):
                return False

            # Create or update policy
            policy_id = await self.create_access_policy(
                owner_did=sharer_did or entry.access_control.get('owner', ''),
                allowed_dids=[target_did],
                permissions=permissions
            )

            logger.info(f"Shared entry {entry_id} with {target_did}")
            return True

        except Exception as e:
            logger.error(f"Failed to share data {entry_id}: {e}")
            return False

    async def sync_with_mesh(self, mesh_network) -> bool:
        """
        Synchronize vault data with mesh network.

        Args:
            mesh_network: Mesh network instance

        Returns:
            True if sync successful
        """
        try:
            # This would implement decentralized sync protocol
            # For now, just log the intent
            logger.info("Synchronizing vault with mesh network")
            return True

        except Exception as e:
            logger.error(f"Mesh sync failed: {e}")
            return False

    def get_vault_stats(self) -> Dict[str, Any]:
        """Get vault statistics."""
        data_types = {}
        for entry in self.entries.values():
            data_types[entry.data_type] = data_types.get(entry.data_type, 0) + 1

        return {
            'total_entries': len(self.entries),
            'data_types': data_types,
            'total_policies': len(self.access_policies),
            'vault_path': str(self.vault_path)
        }


class MeshDataManager:
    """
    Data Manager for Mesh Network Integration.

    Manages different types of mesh data in the vault with
    appropriate access controls and synchronization.
    """

    def __init__(self, vault: Web5DataVault):
        self.vault = vault

    async def store_user_profile(self, user_did: str, profile_data: Dict[str, Any]) -> str:
        """Store user profile data."""
        return await self.vault.store_data(
            'user_profile',
            profile_data,
            {'user_did': user_did},
            user_did
        )

    async def store_mesh_credentials(self, user_did: str, credentials: Dict[str, Any]) -> str:
        """Store mesh network credentials."""
        return await self.vault.store_data(
            'mesh_credentials',
            credentials,
            {'user_did': user_did},
            user_did
        )

    async def store_routing_data(self, user_did: str, routing_info: Dict[str, Any]) -> str:
        """Store routing information."""
        return await self.vault.store_data(
            'routing_data',
            routing_info,
            {'user_did': user_did},
            user_did
        )

    async def store_vote_record(self, user_did: str, vote_data: Dict[str, Any]) -> str:
        """Store voting record."""
        return await self.vault.store_data(
            'vote_record',
            vote_data,
            {'user_did': user_did},
            user_did
        )

    async def get_user_data(self, user_did: str, data_type: str) -> List[Dict[str, Any]]:
        """Get all user data of a specific type."""
        # This would require indexing by user/type
        # For now, return empty list
        return []
