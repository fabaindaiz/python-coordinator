import logging
from typing import Dict, Type
from .service import ServiceManager
from .exception import ExceptionHandler
from .module import BaseModule, ModuleRunner

logger = logging.getLogger(__name__)


class ModuleAlreadyRegisteredError(Exception):
    """Excepción lanzada cuando un módulo ya está registrado."""

class ModuleNotRegisteredError(Exception):
    """Excepción lanzada cuando un módulo no está registrado."""


class ApplicationManager:
    def __init__(self, service_manager: ServiceManager = None, exception_handler: ExceptionHandler = None):
        self.service_manager = service_manager or ServiceManager()
        self.exception_handler = exception_handler or ExceptionHandler()

        self.modules: Dict[str, ModuleRunner] = {}
        self.active = False

    def register_module(self, module: Type[BaseModule]) -> None:
        """Registra un módulo para ser gestionado por el ApplicationManager."""
        name = module.__name__
        if name in self.modules:
            raise ModuleAlreadyRegisteredError(f"Module {name} is already registered.")
        
        runner = ModuleRunner(module, self.service_manager, self.exception_handler)
        self.modules[name] = runner
    
    def unregister_module(self, module: Type[BaseModule]) -> None:
        """Elimina un módulo del ApplicationManager."""
        name = module.__name__
        if not name in self.modules:
            raise ModuleNotRegisteredError(f"Module {name} is not registered.")
        
        self.modules[name].stop()
        del self.modules[name]

    def start_all(self) -> None:
        """Inicia todos los módulos registrados."""
        if self.active:
            logger.warning("Application is already running.")
            return
        
        for name, runner in self.modules.items():
            logger.info(f"Starting {name} module...")
            runner.start()
        
        self.active = True
        logger.info("All modules started.")

    def stop_all(self) -> None:
        """Detiene todos los módulos registrados."""
        if not self.active:
            logger.warning("Application is not running.")
            return
        
        for name, runner in self.modules.items():
            logger.info(f"Stopping {name} module...")
            runner.stop()
        
        self.active = False
        logger.info("All modules stopped.")

    def restart_all(self) -> None:
        """Reinicia todos los módulos registrados."""
        logger.info("Restarting all modules...")
        self.stop_all()
        self.start_all()
