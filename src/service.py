import logging
from functools import wraps
from typing import Any, Callable, Dict, Type, Union
from dependency_injector import providers

logger = logging.getLogger(__name__)


class ServiceAlreadyRegisteredError(Exception):
    """Excepción lanzada cuando un servicio ya está registrado."""

class ServiceNotRegisteredError(Exception):
    """Excepción lanzada cuando un servicio no está registrado."""


class ServiceManager:
    
    def __init__(self) -> None:
        self.services: Dict[Type[Any], Union[providers.Factory, providers.Singleton]] = {}

    def _register(self, constructor: type[Any], service: Type[Any], *args, **kwargs) -> None:
        if service in self.services:
            raise ServiceAlreadyRegisteredError(f"Service {service.__name__} already registered")
        self.services[service] = constructor(service, *args, **kwargs)

    def register_factory(self, service: Type[Any], *args, **kwargs) -> None:
        self._register(providers.Factory, service, *args, **kwargs)
    
    def register_singleton(self, service: Type[Any], *args, **kwargs) -> None:
        self._register(providers.Singleton, service, *args, **kwargs)
    
    def get_service(self, service: Type[Any]) -> object:
        if not service in self.services:
            raise ServiceNotRegisteredError(f"Service {service.__name__} not registered")
        return self.services[service]()
    
    def _injected_services(self, function: Callable) -> Dict[str, object]:
        return {name: self.get_service(service) for name, service in function.__annotations__.items() if service in self.services}
    
    def provide(self, function: Callable) -> None:
        injected_kwargs = self._injected_services(function)
        function(**injected_kwargs)
    
    def inject(self, function: Callable) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs):
            injected_kwargs = self._injected_services(function)
            injected_kwargs.update(kwargs)
            return function(*args, **injected_kwargs)
        return wrapper


if __name__ == "__main__":
    import random
    manager = ServiceManager()
    
    class Service1:
        def __init__(self) -> None:
            self.random_num = random.randint(1000, 9999)
        
        def work(self) -> None:
            print(f"Service1 working with {self.random_num}")
    
    class Service2:
        def __init__(self) -> None:
            self.random_num = random.randint(1000, 9999)
        
        def work(self) -> None:
            print(f"Service2 working with {self.random_num}") 
    
    # Los singleton son servicios que se inyectan como una instancia única
    manager.register_singleton(Service1)

    # Los factory son servicios que se inyectan como una instancia nueva cada vez
    manager.register_factory(Service2)
    
    @manager.inject
    def test1(service1: Service1, service2: Service2) -> None:
        service1.work()
        service2.work()

    @manager.inject
    def test2(service1: Service1, service2: Service2) -> None:
        service1.work()
        service2.work()

    test1()
    test2()
    