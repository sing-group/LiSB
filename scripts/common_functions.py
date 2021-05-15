import json
import sys

from Cryptodome.Cipher import PKCS1_OAEP, AES
from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes


def parse_args(conf_file):
    """
    This function parses the arguments passed to the scripts. In case no arguments are passed, they are loaded from the 'conf/backups.json' file
    :return: the parsed arguments in dictionary format
    """
    n_args = len(sys.argv)
    if n_args == 1:
        # If not passed as parameters, they are read from the conf/backups.json file
        with open(conf_file) as backups_conf_file:
            options = json.load(backups_conf_file)
        if not options:
            raise Exception("The options file needs to be configured")
    else:
        options = {}
        for i in range(1, n_args):
            arg = sys.argv[i].split("=")
            options[arg[0]] = [] if len(arg) == 1 else arg[1].split(",")
    return options


def encrypt_file(unencrypted_path, encrypted_path, public_key_path):
    # Load file to be encrypted
    with open(unencrypted_path, "rb") as unencrypted_file:
        unencrypted = unencrypted_file.read()

    # Load public SSH key to string
    with open(public_key_path) as public_key_file:
        public_key_str = public_key_file.read().split("\n")[0]

    # Create RSA public key and session key
    public_key = RSA.importKey(public_key_str)
    session_key = get_random_bytes(16)

    # Encrypt the session key with the public RSA key
    cipher_rsa = PKCS1_OAEP.new(public_key)
    enc_session_key = cipher_rsa.encrypt(session_key)

    # Encrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(unencrypted)

    with open(encrypted_path, "wb") as encrypted_file:
        for x in (enc_session_key, cipher_aes.nonce, tag, ciphertext):
            encrypted_file.write(x)


def decrypt_file(encrypted_path, decrypted_path, private_key_str):
    # Create private key from string
    private_key = RSA.importKey(private_key_str)

    # Open encrypted file
    with open(encrypted_path, "rb") as encrypted_file:
        enc_session_key, nonce, tag, ciphertext = [encrypted_file.read(x) for x in
                                                   (private_key.size_in_bytes(), 16, 16, -1)]

    # Decrypt the session key with the private RSA key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(enc_session_key)

    # Decrypt the data with the AES session key
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    data = cipher_aes.decrypt_and_verify(ciphertext, tag)

    # Store decrypted file
    with open(decrypted_path, "wb") as decrypted:
        decrypted.write(data)
