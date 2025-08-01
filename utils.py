import datetime
import ipaddress

from cryptography import x509
from cryptography.hazmat._oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_self_signed_cert():
    """Generate a self-signed certificate for HTTPS"""

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Organization"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Write certificate and key to files
    with open("server.crt", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open("server.key", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    print("Self-signed certificate generated: server.crt, server.key")


def convert_value_for_xmlrpc(value):
    """Convert int/float values to string with type markers for XML-RPC transmission"""
    if isinstance(value, bool):
        return value  # Keep booleans as-is, check before int since bool is subclass of int
    elif isinstance(value, int):
        return f"__INT__{value}"
    elif isinstance(value, float):
        return f"__FLOAT__{value}"
    elif isinstance(value, (list, tuple)):
        return [convert_value_for_xmlrpc(item) for item in value]
    elif isinstance(value, dict):
        return {k: convert_value_for_xmlrpc(v) for k, v in value.items()}
    else:
        return value


def convert_value_from_xmlrpc(value):
    """Convert string representations back to int/float, leaving original strings unchanged"""
    if isinstance(value, str):
        if value.startswith("__INT__"):
            try:
                return int(value[7:])  # Remove "__INT__" prefix
            except ValueError:
                return value  # Return unchanged if conversion fails
        elif value.startswith("__FLOAT__"):
            try:
                return float(value[9:])  # Remove "__FLOAT__" prefix
            except ValueError:
                return value  # Return unchanged if conversion fails
        else:
            return value  # Keep original strings as-is
    elif isinstance(value, (list, tuple)):
        return type(value)(convert_value_from_xmlrpc(item) for item in value)
    elif isinstance(value, dict):
        return {k: convert_value_from_xmlrpc(v) for k, v in value.items()}
    else:
        return value


class Data:
    """Utility class for passing args and kwargs to XML-RPC functions"""

    def __init__(self, *args, response_code=None, error=None, result=None, **kwargs):
        # Convert int/float values to strings for XML-RPC transmission
        self.args = [convert_value_for_xmlrpc(arg) for arg in args]
        self.kwargs = {k: convert_value_for_xmlrpc(v) for k, v in kwargs.items()}
        self.timestamp = datetime.datetime.now().isoformat()
        self.response_code = response_code if response_code is not None else 0
        self.error = error
        # Convert result if it's int/float
        self.result = convert_value_for_xmlrpc(result) if result is not None else result
        # Mark this as a Data object for XML-RPC serialization
        self._is_data_object = True

    def get_args(self):
        """Return the args as a tuple"""
        return tuple(self.args)

    def get_kwargs(self):
        """Return the kwargs as a dictionary"""
        return self.kwargs

    def get_result(self):
        """Return the result value"""
        return convert_value_from_xmlrpc(self.result)

    def _get_dict_data(self):
        """Get dictionary representation without None values"""
        data = {
            'args': self.args,
            'kwargs': self.kwargs,
            'timestamp': self.timestamp,
            'response_code': self.response_code,
            'error': self.error,
            'result': self.result,
            '_is_data_object': True
        }
        # Remove any None values to avoid XML-RPC marshalling issues
        return {k: v for k, v in data.items() if v is not None}

    @property
    def __dict__(self):
        """Make the object appear as a dictionary to XML-RPC"""
        return self._get_dict_data()

    def __getstate__(self):
        """Automatically serialize for XML-RPC transmission"""
        return self._get_dict_data()

    def items(self):
        """Make the object iterable like a dictionary for XML-RPC marshalling"""
        return self._get_dict_data().items()

    def keys(self):
        """Dictionary-like interface for XML-RPC"""
        return self._get_dict_data().keys()

    def values(self):
        """Dictionary-like interface for XML-RPC"""
        return self._get_dict_data().values()

    def __getitem__(self, key):
        """Dictionary-like access for XML-RPC"""
        return self._get_dict_data()[key]

    def __repr__(self):
        return f"Data(timestamp={self.timestamp}, response_code={self.response_code}, error={self.error}, result={self.result}, args={self.args}, kwargs={self.kwargs})"
