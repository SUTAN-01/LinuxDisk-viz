import hashlib
from diskviz_api.config import Settings

def test_settings_expose_sha256_not_plaintext():
    s = Settings(read_token="myread", write_token="mywrite")
    assert s.read_token_sha256 == hashlib.sha256(b"myread").hexdigest()
    assert s.write_token_sha256 == hashlib.sha256(b"mywrite").hexdigest()

def test_settings_defaults_unchanged():
    s = Settings()
    assert s.bind_port == 8765
    assert s.max_concurrent_scans == 1
