from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="diskviz_", env_file=".env")
    scanner_binary: Path = Path("disk-scanner")
    cache_path: Path = Path("/var/lib/diskviz/cache.sqlite")
    scans_dir: Path = Path("/var/lib/diskviz/scans")
    audit_log: Path = Path("/var/log/diskviz/audit.jsonl")
    read_token: str = "dev-read"
    write_token: str = "dev-write"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8765
    scan_ttl_seconds: int = 86400
    max_concurrent_scans: int = 1

settings = Settings()
