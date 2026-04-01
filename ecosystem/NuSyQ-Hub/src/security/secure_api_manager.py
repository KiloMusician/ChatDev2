"""Secure API Key Manager.

Handles encrypted storage and secure access to API keys for fallback scenarios.

Provides secure, encrypted storage for API keys while prioritizing offline models
"""

import base64
import json
import os
from pathlib import Path
from typing import cast

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureAPIManager:
    """Secure manager for API keys with encryption."""

    def __init__(self, master_password: str | None = None) -> None:
        """Initialize SecureAPIManager with master_password."""
        self.config_dir = Path.home() / ".kilo-foolish" / "secure"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.key_file = self.config_dir / "encrypted_keys.dat"
        self.salt_file = self.config_dir / "key.salt"

        self.master_password: str = master_password or (
            os.getenv("KILO_MASTER_PASSWORD") or "kilo-foolish-default"
        )
        self._cipher_suite: Fernet | None = None

        self._initialize_encryption()

    def _initialize_encryption(self) -> None:
        """Initialize encryption system."""
        # Generate or load salt
        if self.salt_file.exists():
            salt = self.salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
            self.salt_file.chmod(0o600)  # Secure permissions

        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        self._cipher_suite = Fernet(key)

    def store_api_key(self, provider: str, api_key: str) -> bool:
        """Securely store an API key."""
        try:
            # Load existing keys
            keys = self._load_encrypted_keys()

            # Add new key
            keys[provider] = api_key

            # Encrypt and save
            assert self._cipher_suite is not None
            encrypted_data = self._cipher_suite.encrypt(json.dumps(keys).encode())
            self.key_file.write_bytes(encrypted_data)
            self.key_file.chmod(0o600)  # Secure permissions

            return True
        except (OSError, PermissionError, ValueError):
            return False

    def get_api_key(self, provider: str) -> str | None:
        """Retrieve and decrypt an API key."""
        try:
            keys = self._load_encrypted_keys()
            return keys.get(provider)
        except (KeyError, AttributeError):
            return None

    def _load_encrypted_keys(self) -> dict[str, str]:
        """Load and decrypt stored keys."""
        if not self.key_file.exists():
            return {}

        try:
            encrypted_data = self.key_file.read_bytes()
            assert self._cipher_suite is not None
            decrypted_data = self._cipher_suite.decrypt(encrypted_data)
            return cast(dict[str, str], json.loads(decrypted_data.decode()))
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            return {}

    def list_stored_providers(self) -> list:
        """List providers with stored keys."""
        keys = self._load_encrypted_keys()
        return list(keys.keys())

    def remove_api_key(self, provider: str) -> bool:
        """Remove a stored API key."""
        try:
            keys = self._load_encrypted_keys()
            if provider in keys:
                del keys[provider]
                assert self._cipher_suite is not None
                encrypted_data = self._cipher_suite.encrypt(json.dumps(keys).encode())
                self.key_file.write_bytes(encrypted_data)
                return True
            return False
        except (OSError, PermissionError, ValueError):
            return False


# Convenience functions
def setup_secure_api_keys():
    """Interactive setup for secure API keys."""
    manager = SecureAPIManager()

    providers = {
        "openai": "OpenAI API Key",
        "anthropic": "Anthropic API Key",
        "google": "Google AI API Key",
        "cohere": "Cohere API Key",
    }

    for provider, description in providers.items():
        current_key = manager.get_api_key(provider)
        if current_key:
            continue

        # Check environment variable first
        env_key = os.getenv(f"{provider.upper()}_API_KEY")
        if env_key:
            manager.store_api_key(provider, env_key)
            continue

        # Interactive input
        api_key = input(f"Enter {description} (or press Enter to skip): ").strip()
        if api_key:
            manager.store_api_key(provider, api_key)
        else:
            pass

    return manager


# Global manager instance
_secure_manager = None


def get_secure_api_manager() -> SecureAPIManager:
    """Get global secure API manager."""
    global _secure_manager
    if _secure_manager is None:
        _secure_manager = SecureAPIManager()
    return _secure_manager
