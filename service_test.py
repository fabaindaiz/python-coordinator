import time
import random
import logging
from src.manager import ApplicationManager
from src.exception import ExceptionAction
from src.service import ServiceManager
from src.module import ModuleRunner, BaseModule

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])


class RetryException(Exception):
    """Una excepción que indica que una operación debe reintentarse."""
    action = ExceptionAction.RETRY


class Service1:

    def __init__(self) -> None:
        self.random_num = random.randint(1000, 9999)
    
    def work(self) -> None:
        print(f"Service1 working with {self.random_num}", flush=True)

class Service2:

    def __init__(self) -> None:
        self.random_num = random.randint(1000, 9999)
    
    def work(self) -> None:
        print(f"Service2 working with {self.random_num}", flush=True)


class Module1(BaseModule):

    def __init__(self, runner: ModuleRunner) -> None:
        runner.service.provide(self.services)

    def services(self, service1: Service1, service2: Service2) -> None:
        self.service1 = service1
        self.service2 = service2
    
    def on_start(self) -> None:
        self.service1.work()
        self.service2.work()
        time.sleep(3)
    
    def run(self):
        self.service1.work()
        self.service2.work()

        if random.randint(1, 10) == 1:
            raise RetryException("Random retry exception")

class Module2(BaseModule):

    def __init__(self, runner: ModuleRunner) -> None:
        runner.service.provide(self.services)
    
    def services(self, service1: Service1, service2: Service2) -> None:
        service1.work()
        service2.work()

    def on_start(self) -> None:
        time.sleep(3)

    def run (self):
        pass


if __name__ == "__main__":
    service_manager = ServiceManager()
    service_manager.register_singleton(Service1)
    service_manager.register_factory(Service2)

    app_manager = ApplicationManager(service_manager)
    app_manager.register_module(Module1)
    app_manager.register_module(Module2)

    print("Starting application")
    app_manager.start_all()

    time.sleep(30)

    print("Stopping application")
    app_manager.stop_all()
