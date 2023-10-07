import logging
import backoff
from enum import Enum, auto
from typing import Callable, Dict, Type

logger = logging.getLogger(__name__)


class ExceptionAction(Enum):
    CONTINUE = auto()
    RETRY = auto()
    RAISE = auto()
    LOG_AND_CONTINUE = auto()
    LOG_AND_RETRY = auto()
    SUPPRESS = auto()  # Suprimir el error sin hacer nada
    CUSTOM = auto()  # Permite al usuario definir un comportamiento personalizado


class ExceptionHandler:

    def __init__(self) -> None:
        # Mapa de excepciones a acciones generales
        # El valor default es RAISE, pero puede ser personalizado al inicializar
        self.exception_behavior: Dict[Type[Exception], ExceptionAction] = {}
    
    def set_exception_behavior(self, exception_type: Type[Exception], behavior: ExceptionAction) -> None:
        """Establece el comportamiento para una excepción específica."""
        self.exception_behavior[exception_type] = behavior
    
    def get_exception_behavior(self, exception_type: Type[Exception]) -> ExceptionAction:
        """Obtiene el comportamiento para una excepción específica."""
        return self.exception_behavior.get(exception_type, ExceptionAction.RAISE)


    def handle_exception(self, exception: Exception) -> None:
        action = self.get_exception_behavior(type(exception))

        if action in [ExceptionAction.RETRY, ExceptionAction.LOG_AND_RETRY]:
            if action == ExceptionAction.LOG_AND_RETRY:
                logger.error(f"Error: {exception}. Retrying...")
            raise exception
        elif action == ExceptionAction.LOG_AND_CONTINUE:
            logger.error(f"Error: {exception}. Continuing...")
            return
        elif action == ExceptionAction.SUPPRESS:
            return
        else:
            raise exception
        
    def _need_retry(self, exception: Exception) -> bool:
        """Determina si necesita reintentar basado en la excepción."""
        action = self.get_exception_behavior(type(exception))
        return action in [ExceptionAction.RETRY, ExceptionAction.LOG_AND_RETRY]
    
    def handle(self, function: Callable, *args, **kwargs) -> None:
        @backoff.on_exception(backoff.expo,
                              Exception,
                              max_tries=10,
                              giveup=lambda e: not self._need_retry(e))
        def wrapped_function():
            try:
                return function(*args, **kwargs)
            except Exception as exception:
                self.handle_exception(exception)
        wrapped_function()


if __name__ == "__main__":
    import random

    def fetch_data_from_server():
        rnd = random.randint(1, 3)
        
        if rnd == 1:
            raise TimeoutError("Server did not respond!")
        elif rnd == 2:
            raise ValueError("Received unexpected data!")
        elif rnd == 3:
            raise PermissionError("You do not have permission to access this data!")
        
        return "Successful Data"


    # Configuramos nuestro ExceptionHandler
    handler = ExceptionHandler()
    handler.set_exception_behavior(TimeoutError, ExceptionAction.RETRY)
    handler.set_exception_behavior(ValueError, ExceptionAction.LOG_AND_CONTINUE)
    handler.set_exception_behavior(PermissionError, ExceptionAction.SUPPRESS)

    # Ahora, intentamos obtener datos del servidor
    exception = handler.handle(fetch_data_from_server)

    if exception:
        logger.error(f"Final error after handling: {exception}")
    else:
        print("Data fetched successfully!")
