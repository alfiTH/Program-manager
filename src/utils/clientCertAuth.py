import datetime
import json
import os
import re

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

CA_DIR = "certificates"
CA_CERT_PATH = os.path.join(CA_DIR, "ca_cert.pem")
CA_KEY_PATH = os.path.join(CA_DIR, "ca_key.pem")
CLIENT_CERTS_DIR = "client_certs"
REGISTRY_FILE = "client_certs.json"

CA_VALIDITY_DAYS = 20 * 365
CLIENT_CERT_VALIDITY_DAYS = 5 * 365


def _load_registry() -> dict:
    if not os.path.isfile(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def _save_registry(data: dict) -> None:
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)


def ensure_ca() -> str:
    """Crea la CA privada del servidor si no existe. Devuelve la ruta al certificado de la CA."""
    if os.path.isfile(CA_CERT_PATH) and os.path.isfile(CA_KEY_PATH):
        return CA_CERT_PATH

    os.makedirs(CA_DIR, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Program Manager Client CA"),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=CA_VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=True,
                crl_sign=True, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    with open(CA_KEY_PATH, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    os.chmod(CA_KEY_PATH, 0o600)

    with open(CA_CERT_PATH, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return CA_CERT_PATH


def _sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def issue_client_cert(username: str, label: str, p12_password: str) -> str:
    """Genera un certificado de cliente firmado por la CA para `username` y lo exporta
    como .p12 protegido con `p12_password`. Devuelve la ruta del archivo .p12 generado."""
    ensure_ca()

    with open(CA_KEY_PATH, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)
    with open(CA_CERT_PATH, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, username)])
    now = datetime.datetime.now(datetime.timezone.utc)
    serial = x509.random_serial_number()
    client_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(client_key.public_key())
        .serial_number(serial)
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=CLIENT_CERT_VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    os.makedirs(CLIENT_CERTS_DIR, exist_ok=True)
    p12_bytes = pkcs12.serialize_key_and_certificates(
        name=username.encode(),
        key=client_key,
        cert=client_cert,
        cas=[ca_cert],
        encryption_algorithm=serialization.BestAvailableEncryption(p12_password.encode()),
    )

    serial_hex = format(serial, "x")
    filename = f"{_sanitize(username)}-{_sanitize(label)}.p12"
    path = os.path.join(CLIENT_CERTS_DIR, filename)
    with open(path, "wb") as f:
        f.write(p12_bytes)
    os.chmod(path, 0o600)

    registry = _load_registry()
    registry[serial_hex] = {
        "username": username,
        "label": label,
        "issued_at": now.isoformat(),
        "revoked": False,
    }
    _save_registry(registry)

    return path


def list_client_certs(username: str = None) -> list[dict]:
    registry = _load_registry()
    certs = [{"serial": serial, **record} for serial, record in registry.items()]
    if username is not None:
        certs = [c for c in certs if c["username"] == username]
    return certs


def revoke_client_cert(serial_hex: str) -> bool:
    registry = _load_registry()
    if serial_hex not in registry:
        return False
    registry[serial_hex]["revoked"] = True
    _save_registry(registry)
    return True


def identify_client_cert(pem_text: str) -> str | None:
    """A partir del PEM del certificado de cliente ya validado por la capa TLS
    (cadena de confianza contra nuestra CA), extrae el usuario si el certificado
    sigue activo (no revocado) en el registro. Devuelve None si no aplica."""
    try:
        cert = x509.load_pem_x509_certificate(pem_text.encode())
    except ValueError:
        return None

    serial_hex = format(cert.serial_number, "x")
    registry = _load_registry()
    record = registry.get(serial_hex)
    if record is None or record.get("revoked"):
        return None

    cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    if not cn_attrs:
        return None
    cn = cn_attrs[0].value

    if cn != record["username"]:
        return None

    return cn
