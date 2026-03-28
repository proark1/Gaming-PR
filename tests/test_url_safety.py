"""Tests for SSRF protection utility."""

from app.utils.url_safety import is_safe_url


def test_safe_https_url():
    assert is_safe_url("https://hooks.slack.com/test") is True


def test_safe_http_url():
    assert is_safe_url("http://example.com/webhook") is True


def test_block_localhost():
    assert is_safe_url("http://localhost:5432/") is False


def test_block_loopback_ip():
    assert is_safe_url("http://127.0.0.1:8080/") is False


def test_block_private_10():
    assert is_safe_url("http://10.0.0.1/admin") is False


def test_block_private_172():
    assert is_safe_url("http://172.16.0.1/") is False


def test_block_private_192():
    assert is_safe_url("http://192.168.1.1/") is False


def test_block_metadata_ip():
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False


def test_block_metadata_hostname():
    assert is_safe_url("http://metadata.google.internal/computeMetadata/v1/") is False


def test_block_file_scheme():
    assert is_safe_url("file:///etc/passwd") is False


def test_block_ftp_scheme():
    assert is_safe_url("ftp://internal.server/data") is False


def test_block_empty_url():
    assert is_safe_url("") is False


def test_block_no_scheme():
    assert is_safe_url("just-a-string") is False
