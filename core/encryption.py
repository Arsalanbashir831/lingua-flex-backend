from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

class EncryptionError(Exception):
    pass

def get_encryptor():
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", None)
    if not key:
        if not settings.DEBUG:
            raise ImproperlyConfigured(
                "FIELD_ENCRYPTION_KEY must be set in production to ensure data security. "
                "Data will NOT be saved in plaintext for sensitive fields."
            )
        # Fallback to local default for development if not set
        logger.warning("FIELD_ENCRYPTION_KEY is not set. Data will not be encrypted properly.")
        return None
    try:
        return Fernet(key.encode())
    except Exception as e:
        logger.error(f"Failed to initialize Fernet with provided key: {e}")
        return None

def encrypt_value(value: str) -> str:
    if not value:
        return value
    encryptor = get_encryptor()
    if not encryptor:
        return value
    return encryptor.encrypt(value.encode()).decode()

def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    encryptor = get_encryptor()
    if not encryptor:
        return ciphertext
    try:
        return encryptor.decrypt(ciphertext.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return ciphertext
