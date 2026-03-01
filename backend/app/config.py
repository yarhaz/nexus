from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8", extra="ignore")

    # App
    environment: str = "development"
    debug: bool = False
    secret_key: str = "dev-secret-key"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Azure Entra ID
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # Cosmos DB Gremlin
    cosmos_endpoint: str = "wss://localhost:8901/gremlin"
    cosmos_key: str = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
    cosmos_database: str = "nexus"
    cosmos_container: str = "main"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Key Vault
    key_vault_url: str = ""

    # OpenTelemetry
    otel_enabled: bool = False
    applicationinsights_connection_string: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Webhooks
    github_webhook_secret: str = "dev-webhook-secret"
    github_token: str = ""
    ado_webhook_secret: str = "dev-ado-secret"

    # Azure Web PubSub (Phase 1 — real-time updates)
    webpubsub_connection_string: str = ""
    webpubsub_hub_name: str = "nexus"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
