from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    dataset_service_url: str = os.getenv("DATASET_SERVICE_URL", "http://dataset_service:8000")
    x_bearer_token: str | None = os.getenv("TWEEPY_BEARER_TOKEN") or os.getenv("X_BEARER_TOKEN")
    nominatim_base_url: str = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")
    nominatim_user_agent: str = os.getenv(
        "NOMINATIM_USER_AGENT", "social-mapping/1.0 (+https://github.com/osint-services/social_mapping)"
    )
    geocoder_cache_path: str = os.getenv("GEOCODER_CACHE_PATH", "/data/geocoder-cache.db")
    geocoder_cache_days: int = int(os.getenv("GEOCODER_CACHE_DAYS", "30"))
    geocoder_min_interval_seconds: float = float(os.getenv("GEOCODER_MIN_INTERVAL_SECONDS", "1"))
    provider_timeout_seconds: float = float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "15"))


settings = Settings()
