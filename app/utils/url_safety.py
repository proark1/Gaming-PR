"""
URL validation utilities to prevent SSRF attacks.

Used by webhook delivery, contact scraper, sitemap fetcher, and
any code that makes HTTP requests to user-provided URLs.
"""
import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Private/reserved IP ranges that should never be targeted
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private A
    ipaddress.ip_network("172.16.0.0/12"),      # Private B
    ipaddress.ip_network("192.168.0.0/16"),     # Private C
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 private
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]

_BLOCKED_HOSTS = {
    "localhost",
    "metadata.google.internal",     # GCP metadata
    "169.254.169.254",              # AWS/Azure/GCP metadata
}


def is_safe_url(url: str) -> bool:
    """Check if a URL is safe to fetch (not targeting internal services)."""
    try:
        parsed = urlparse(url)

        # Must be http or https
        if parsed.scheme not in ("http", "https"):
            logger.debug(f"Blocked non-HTTP scheme: {parsed.scheme}")
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Block known dangerous hostnames
        if hostname.lower() in _BLOCKED_HOSTS:
            logger.debug(f"Blocked hostname: {hostname}")
            return False

        # Try to resolve and check if IP is private
        try:
            ip = ipaddress.ip_address(hostname)
            if _is_private_ip(ip):
                logger.debug(f"Blocked private IP: {ip}")
                return False
        except ValueError:
            # Not an IP literal — resolve the hostname
            try:
                resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
                for family, _, _, _, addr in resolved:
                    ip = ipaddress.ip_address(addr[0])
                    if _is_private_ip(ip):
                        logger.debug(f"Blocked resolved private IP: {hostname} -> {ip}")
                        return False
            except socket.gaierror:
                pass  # DNS resolution failed — allow, will fail on fetch anyway

        return True
    except Exception:
        return False


def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address is in a private/reserved range."""
    for network in _BLOCKED_NETWORKS:
        if ip in network:
            return True
    return False
