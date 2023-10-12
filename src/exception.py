import logging
import backoff
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional, Type

logger = logging.getLogger(__name__)


class ExceptionAction(Enum):
    CONTINUE = auto()
    RETRY = auto()
    RAISE = auto()
    LOG_AND_CONTINUE = auto()
    LOG_AND_RETRY = auto()
    CUSTOM = auto()  # Permite al usuario definir un comportamiento personalizado


class ExceptionHandler:

    def __init__(self) -> None:
        self.exception_behavior: Dict[Type[Exception], ExceptionAction] = {}
        self.custom_handlers: Dict[Type[Exception], Callable] = {}
    
    def set_exception_behavior(self, exception: Exception, behavior: ExceptionAction, custom_handler: Optional[Callable] = None) -> None:
        """Establece el comportamiento para una excepción específica."""
        self.exception_behavior[type(exception)] = behavior
        if behavior == ExceptionAction.CUSTOM and custom_handler:
            self.custom_handlers[type(exception)] = custom_handler
    
    def get_exception_behavior(self, exception: Exception) -> ExceptionAction:
        """Obtiene el comportamiento para una excepción específica."""
        behavior = self.exception_behavior.get(type(exception), ExceptionAction.RAISE)
        return exception.__dict__.get("action", behavior)

    def handle_exception(self, exception: Exception) -> None:
        action = self.get_exception_behavior(exception)

        if action == ExceptionAction.CONTINUE:
            return
        
        if action == ExceptionAction.LOG_AND_CONTINUE:
            logger.error(f"Error: {exception}. Continuing...")
            return
        
        if action == ExceptionAction.LOG_AND_RETRY:
            logger.error(f"Error: {exception}. Retrying...")
            raise exception
        
        if action == ExceptionAction.CUSTOM:
            custom_handler = self.custom_handlers.get(type(exception))
            return custom_handler(exception) if custom_handler else None
        
        raise exception
        
    def _exception_giveup(self, exception: Exception) -> bool:
        """Determina si necesita reintentar basado en la excepción."""
        action = self.get_exception_behavior(exception)
        return not action  in [ExceptionAction.RETRY, ExceptionAction.LOG_AND_RETRY]
    
    def handle(self, function: Callable, max_tries: int = 10, *args, **kwargs) -> Any:
        @backoff.on_exception(backoff.expo,
                              Exception,
                              max_tries=max_tries,
                              giveup=self._exception_giveup)
        def wrapped_function():
            try:
                return function(*args, **kwargs)
            except Exception as exception:
                self.handle_exception(exception)
        return wrapped_function()


if __name__ == "__main__":
    import random

    def fetch_data_from_server():
        rnd = random.randint(1, 4)
        
        if rnd == 1:
            raise TimeoutError("Server did not respond!")
        elif rnd == 2:
            raise ValueError("Received unexpected data!")
        elif rnd == 3:
            raise PermissionError("You do not have permission to access this data!")
        
        return "Successful Data Fetch!"


    # Configuramos nuestro ExceptionHandler
    handler = ExceptionHandler()
    handler.set_exception_behavior(TimeoutError, ExceptionAction.RETRY)
    handler.set_exception_behavior(ValueError, ExceptionAction.LOG_AND_CONTINUE)
    handler.set_exception_behavior(PermissionError, ExceptionAction.RAISE)

    # Ahora, intentamos obtener datos del servidor
    exception = handler.handle(fetch_data_from_server)

    if exception:
        logger.error(f"Final error after handling: {exception}")
    else:
        print("Data fetched successfully!")
