import logging
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
        self.exception_map: Dict[Type[Exception], ExceptionAction] = {}
    
    def set_exception_behavior(self, exception_type: Type[Exception], behavior: ExceptionAction) -> None:
        """Establece el comportamiento para una excepción específica."""
        self.exception_map[exception_type] = behavior

    def handle_exception(self, exception: Exception) -> None:
        action = self.exception_map.get(type(exception), ExceptionAction.RAISE)

        if action == ExceptionAction.RETRY:
            raise exception
        elif action == ExceptionAction.LOG_AND_RETRY:
            logger.error(f"Error: {exception}. Retrying...")
            raise exception
        elif action == ExceptionAction.LOG_AND_CONTINUE:
            logger.error(f"Error: {exception}. Continuing...")
            return
        elif action == ExceptionAction.SUPPRESS:
            return
        else:
            raise exception
    
    def handle(self, function: Callable, args=[], kwargs={}, max_retries: int = 10) -> None:
        for _ in range(max_retries):
            try:
                function(*args, **kwargs)
                return
            except Exception as e:
                action = self.exception_map.get(type(e), ExceptionAction.RAISE)

                if action in [ExceptionAction.RETRY, ExceptionAction.LOG_AND_RETRY]:
                    if action == ExceptionAction.LOG_AND_RETRY:
                        logger.error(f"Error: {e}. Retrying...")
                    continue
                elif action == ExceptionAction.LOG_AND_CONTINUE:
                    logger.error(f"Error: {e}. Continuing...")
                    return
                elif action == ExceptionAction.SUPPRESS:
                    return
                else:
                    raise e
        else:
            raise Exception("Max retries reached")


if __name__ == "__main__":
    import random

    def fetch_data_from_server():
        rnd = random.randint(1, 6)
        
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
