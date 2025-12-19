from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from utility.logger import get_logger

class Tool(ABC):
    """Base class for all tools in the MineGuard AI system."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"tool.{name}")

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Execute the tool's primary logic."""
        pass

    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.info(message, extra={"extra": extra} if extra else None)

    def log_error(self, message: str, error: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        log_extra = extra or {}
        if error:
            log_extra["error"] = str(error)
        self.logger.error(message, extra={"extra": log_extra} if log_extra else None)
