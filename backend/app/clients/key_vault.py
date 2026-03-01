from typing import Any
import structlog
from app.config import get_settings

logger = structlog.get_logger()


def get_secret(name: str) -> str | None:
    settings = get_settings()
    if not settings.key_vault_url:
        logger.debug("key_vault.disabled", secret=name)
        return None
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=settings.key_vault_url, credential=credential)
        secret = client.get_secret(name)
        return secret.value
    except Exception as e:
        logger.warning("key_vault.error", secret=name, error=str(e))
        return None
