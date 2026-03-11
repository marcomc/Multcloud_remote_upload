"""MultCloud CLI - Unofficial Python client for MultCloud's internal API."""

# Suppress urllib3 NotOpenSSLWarning (macOS system Python uses LibreSSL)
# Must be set before urllib3 is imported by requests
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*only supports OpenSSL.*")

__version__ = "5.0.0"
