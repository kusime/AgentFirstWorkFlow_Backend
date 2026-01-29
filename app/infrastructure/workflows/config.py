import os
from typing import Optional

class WorkerConfig:
    @property
    def temporal_host(self) -> str:
        return os.getenv("TEMPORAL_HOST", "localhost:7233")
    
    @property
    def enabled_domains(self) -> list[str]:
        """
        Returns a list of python module paths to load as domains.
        Example Env: ENABLE_DOMAINS="app.domains.pizza,app.domains.hello"
        """
        raw = os.getenv("ENABLE_DOMAINS", "")
        if not raw:
            return []
        return [d.strip() for d in raw.split(",") if d.strip()]

config = WorkerConfig()
