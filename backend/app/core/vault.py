import os
import hvac
from typing import Dict, Any, Optional
from app.core.logger import logger

class VaultClient:
    """Helper to fetch secrets from Hashicorp Vault"""
    
    def __init__(self):
        self.url = os.getenv("VAULT_URL", "http://casmarts-core-vault:8200")
        self.token = os.getenv("VAULT_TOKEN", "root")
        self.client = None
        
        if self.token:
            try:
                self.client = hvac.Client(url=self.url, token=self.token)
                if not self.client.is_authenticated():
                    logger.warning("⚠️ Vault client not authenticated")
                    self.client = None
            except Exception as e:
                logger.error(f"❌ Error connecting to Vault: {e}")
                self.client = None

    def get_secrets(self, path: str = "secret/data/consulta-smart") -> Dict[str, Any]:
        """Fetch secrets from KV v2 engine"""
        if not self.client:
            return {}
            
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path.replace("secret/data/", ""))
            return response['data']['data']
        except Exception as e:
            logger.error(f"❌ Error reading from Vault ({path}): {e}")
            return {}

vault_client = VaultClient()
