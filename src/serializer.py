import base64
import pickle


class StateSaver:
    def __init__(self, obj, *attributes):
        self.obj = obj
        self.attributes = attributes

        self._state = None

    def __get__(self, instance, owner):
        return self

    def save_state(self):
        """Guarda el estado del objeto en memoria."""
        if not self._state:
            raise ValueError("State has not been saved yet.")
        self._state = {attr: getattr(self.obj, attr) for attr in self.attributes}

    def restore_state(self):
        """Restaura el estado del objeto desde memoria."""
        for attr, value in self._state.items():
            setattr(self.obj, attr, value)
    
    def to_string(self) -> str:
        """Serializa el estado del objeto a una cadena que puede ser almacenada en una base de datos."""
        binary_data = pickle.dumps(self._state)
        return base64.b64encode(binary_data).decode('utf-8')

    def from_string(self, data_str: str):
        """Deserializa el estado del objeto desde una cadena obtenida de una base de datos."""
        binary_data = base64.b64decode(data_str.encode('utf-8'))
        self._state = pickle.loads(binary_data)
        self.restore_state()

    def to_file(self, filename):
        """Guarda el estado del objeto en un archivo."""
        with open(filename, 'wb') as file:
            pickle.dump(self._state, file)

    def from_file(self, filename):
        """Restaura el estado del objeto desde un archivo."""
        try:
            with open(filename, 'rb') as file:
                self._state = pickle.load(file)
            self.restore_state()
        except (FileNotFoundError, PermissionError) as e:
            raise e from None


if __name__ == "__main__":

    class MyClass:

        def __init__(self):
            self.state_saver = StateSaver(self, "var1", "var3")

            self.var1 = "Hello"
            self.var2 = "World"
            self.var3 = 123

        @property
        def state(self):
            return self.state_saver

        @state.setter
        def state(self, saver):
            saver.obj = self
            self.state_saver = saver


    obj = MyClass()

    # Guardar estado en memoria
    obj.state.save_state()

    # Modificar los atributos
    obj.var1 = "Hola"
    obj.var3 = 456

    # Restaurar el estado desde memoria
    obj.state.restore_state()
    print(obj.var1)  # Debería imprimir "Hello"
    print(obj.var3)  # Debería imprimir "123"

    # Guardar estado en un string
    text = obj.state.to_string()
    print(text)

    # Modificar los atributos nuevamente
    obj.var1 = "Bonjour"
    obj.var3 = 789

    # Restaurar el estado desde el string
    obj.state.from_string(text)
    print(obj.var1)  # Debería imprimir "Hello"
    print(obj.var3)  # Debería imprimir "123"

    # Guardar estado en archivo
    obj.state.to_file("state.pkl")

    # Modificar los atributos nuevamente
    obj.var1 = "Hello"
    obj.var3 = 164

    # Restaurar el estado desde el archivo
    obj.state.from_file("state.pkl")
    print(obj.var1)  # Debería imprimir "Hello"
    print(obj.var3)  # Debería imprimir "123"
