import base64
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad


def encrypt_file(unencrypted_path, encrypted_path):
    # Load file to be encrypted
    with open(unencrypted_path, "rb") as unencrypted_file:
        unencrypted = unencrypted_file.read()

    # Generate encryption key (256 bits)
    key = get_random_bytes(32)

    # Encrypt the data with the AES session key
    cipher_aes = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher_aes.encrypt(pad(unencrypted, AES.block_size))

    with open(encrypted_path, "wb") as encrypted_file:
        encrypted_file.write(cipher_aes.iv)
        encrypted_file.write(ciphertext)

    return base64.b64encode(key)


def decrypt_file(encrypted_path, decrypted_path, base64_key):
    key = base64.b64decode(base64_key)

    # Open encrypted file
    with open(encrypted_path, "rb") as encrypted_file:
        # Read the iv out - this is 16 bytes long
        iv = encrypted_file.read(16)
        # Read the rest
        ciphertext = encrypted_file.read()

    # Decrypt the data
    cipher_aes = AES.new(key, AES.MODE_CBC, iv=iv)
    data = unpad(cipher_aes.decrypt(ciphertext), AES.block_size)

    # Store decrypted file
    with open(decrypted_path, "wb") as decrypted:
        decrypted.write(data)
