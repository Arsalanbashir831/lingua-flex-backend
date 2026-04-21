from django.db import models
from core.encryption import encrypt_value, decrypt_value

class EncryptedCharField(models.TextField):
    description = "A field that stores encrypted character data in the database"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None or not isinstance(value, str):
            return value
        # If it looks like ciphertext (and decryption works), it might already be decrypted 
        # but to_python is called during serialization etc.
        # Standard implementation of from_db_value + to_python ensures it works correctly.
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_value(str(value))

class EncryptedIntegerField(models.TextField):
    description = "A field that stores encrypted integer data as text in the database"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        decrypted = decrypt_value(value)
        try:
            return int(decrypted)
        except (ValueError, TypeError):
            return decrypted

    def to_python(self, value):
        if value is None:
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_value(str(value))
