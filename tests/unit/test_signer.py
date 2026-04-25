from __future__ import annotations

import base64

import pytest

pytest.importorskip("cryptography")
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa

signer_module = pytest.importorskip("gmgn_sdk.signer")

UnsupportedKeyTypeError = signer_module.UnsupportedKeyTypeError
detect_sign_algorithm = signer_module.detect_sign_algorithm
sign_message = signer_module.sign_message


pytestmark = pytest.mark.unit


MESSAGE = "message-to-sign"


def test_sign_message_supports_ed25519() -> None:
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    signature = base64.b64decode(sign_message(MESSAGE, private_key_pem))

    private_key.public_key().verify(signature, MESSAGE.encode("utf-8"))


def test_sign_message_supports_rsa_pss_sha256() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    signature = base64.b64decode(sign_message(MESSAGE, private_key_pem))

    private_key.public_key().verify(
        signature,
        MESSAGE.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
        hashes.SHA256(),
    )


def test_detect_sign_algorithm_rejects_unsupported_keys() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    with pytest.raises(UnsupportedKeyTypeError, match="Unsupported key type"):
        detect_sign_algorithm(private_key_pem)


def test_sign_message_rejects_unsupported_keys() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    with pytest.raises(UnsupportedKeyTypeError, match="Unsupported key type"):
        sign_message(MESSAGE, private_key_pem)
