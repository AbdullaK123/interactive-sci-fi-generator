from typing import Dict, Any, Optional

class ServiceRegistry:
    """Registry for all service instances"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            cls._instance._services = {}
        return cls._instance
    
    def register(self, name: str, service: Any) -> None:
        """Register a service"""
        self._services[name] = service
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return self._services.get(name)
    
    def has(self, name: str) -> bool:
        """Check if a service exists"""
        return name in self._services

# Singleton instance
registry = ServiceRegistry()