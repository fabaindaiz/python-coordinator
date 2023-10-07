import time
import logging
import threading
from typing import Type
from src.service import ServiceManager
from src.exception import ExceptionAction, ExceptionHandler

logger = logging.getLogger(__name__)


class BaseModule:

    def __init__(self, service: ServiceManager, exception: ExceptionHandler) -> None:
        pass

    def on_start(self):
        """Acciones a realizar cuando el módulo se inicia."""
        pass

    def on_stop(self):
        """Acciones a realizar cuando el módulo se detiene."""
        pass

    def run(self):
        """Cuerpo principal del módulo."""
        pass

    def heartbeat(self):
        """Método para notificar que el módulo sigue funcionando."""
        pass


class ModuleRunner:
    def __init__(self, module: Type[BaseModule], service: ServiceManager, exception: ExceptionHandler, *args, **kwargs) -> None:
        self.module: Type[BaseModule] = module
        self.service: ServiceManager = service
        self.exception: ExceptionHandler = exception
        self.args: list = args
        self.kwargs: dict = kwargs
        
        self.module_thread: threading.Thread = None
        self.thread_active: bool = False
        self.watchdog_thread: threading.Thread = None
        self.watchdog_active: bool = False
        self.heartbeat_event: threading.Event = threading.Event()

    def _runner(self) -> None:
        try:
            instance = self.module(self.service, self.exception, *self.args, **self.kwargs)
            instance.on_start()
            while self.thread_active:
                instance.run()
                instance.heartbeat()
                self.heartbeat_event.set()
                time.sleep(1)
            instance.on_stop()
        except Exception as exception:
            self.exception.handle_exception(exception)

    def _watchdog(self) -> None:
        while self.watchdog_active:
            if not self.heartbeat_event.wait(timeout=10):
                logger.error(f"Module {self.module.__name__} seems unresponsive. Restarting...")
                if self.watchdog_active:
                    self.restart(watchdog=False)
            self.heartbeat_event.clear()

    def start(self, watchdog=True) -> None:
        if self.thread_active:
            logger.warning(f"Module {self.module.__name__} is already running.")
            return
        
        self.module_thread = threading.Thread(target=self._runner)
        self.module_thread.start()
        self.thread_active = True
        
        if watchdog:
            self.watchdog_active = True
            self.watchdog_thread = threading.Thread(target=self._watchdog)
            self.watchdog_thread.start()

        logger.info(f"Module {self.module.__name__} started.")

    def stop(self, watchdog=True) -> None:
        if not self.thread_active:
            logger.warning(f"Module {self.module.__name__} is not running.")
            return
        
        if watchdog:
            self.watchdog_active = False
            self.watchdog_thread.join()
        
        self.thread_active = False
        self.module_thread.join()

    def restart(self, watchdog=True) -> None:
        self.stop(watchdog)
        self.start(watchdog)


if __name__=="__main__":
    import random

    class PingModule(BaseModule):

        def run(self):
            print('Ping!', flush=True)
            logger.info("Ping!")

    class UnstableModule(BaseModule):

        def run(self):
            if random.randint(1, 10) == 5: # Ocasionalmente, falla
                raise ValueError("Oops, something went wrong!")
            print('Working...', flush=True)
            logger.info("Working...")

    # Configuramos el ExceptionHandler
    handler = ExceptionHandler()
    handler.set_exception_behavior(ValueError, ExceptionAction.LOG_AND_RETRY)

    # Crear runners para los módulos
    ping_runner = ModuleRunner(PingModule, handler)
    unstable_runner = ModuleRunner(UnstableModule, handler)

    # Iniciar los runners
    ping_runner.start()
    unstable_runner.start()

    # Para el propósito de este ejemplo, dejamos que los módulos se ejecuten por 30 segundos
    time.sleep(30)

    # Detener los runners
    ping_runner.stop()
    unstable_runner.stop()
