"""Private-key detection and signing for GMGN critical auth."""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

SignAlgorithm = str


class UnsupportedKeyTypeError(ValueError):
    """Raised when the provided key is neither Ed25519 nor RSA."""


def load_private_key(key_path: str | Path) -> str:
    return Path(key_path).expanduser().resolve().read_text(encoding="utf-8")


def _load_key(private_key_pem: str) -> ed25519.Ed25519PrivateKey | rsa.RSAPrivateKey:
    key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    if isinstance(key, ed25519.Ed25519PrivateKey | rsa.RSAPrivateKey):
        return key
    raise UnsupportedKeyTypeError(
        f"Unsupported key type: {type(key).__name__}. Supported: Ed25519, RSA"
    )


def detect_sign_algorithm(private_key_pem: str) -> SignAlgorithm:
    key = _load_key(private_key_pem)
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return "Ed25519"
    if isinstance(key, rsa.RSAPrivateKey):
        return "RSA-SHA256"
    raise UnsupportedKeyTypeError(
        f"Unsupported key type: {type(key).__name__}. Supported: Ed25519, RSA"
    )


def sign_message(message: str, private_key_pem: str, algorithm: SignAlgorithm | None = None) -> str:
    key = _load_key(private_key_pem)
    selected = algorithm or detect_sign_algorithm(private_key_pem)
    msg = message.encode("utf-8")

    if selected == "Ed25519":
        if not isinstance(key, ed25519.Ed25519PrivateKey):
            raise ValueError("Private key is not Ed25519")
        signature = key.sign(msg)
    elif selected == "RSA-SHA256":
        if not isinstance(key, rsa.RSAPrivateKey):
            raise ValueError("Private key is not RSA")
        signature = key.sign(
            msg,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    else:
        raise ValueError(f"Unsupported signing algorithm: {selected}")

    return base64.b64encode(signature).decode("ascii")


def detect_algorithm(private_key_pem: str) -> SignAlgorithm:
    return detect_sign_algorithm(private_key_pem)


def sign(message: str, private_key_pem: str, algorithm: SignAlgorithm | None = None) -> str:
    return sign_message(message, private_key_pem, algorithm)
