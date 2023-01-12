# Qt libraries
from PySide6 import QtWidgets

from typing import Any, Callable


def load_ui_file(file: str) -> QtWidgets:
    """
    Loads a .ui file using QUiLoader

    :param file: Filepath of the .ui file
    :return: a QtWidget object. Use window.show()
    """

    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile

    _loader = QUiLoader()
    _ui_file = QFile(file)
    _window = _loader.load(_ui_file)

    return _window


class IOHandler(object):
    input_types = {"QLineEdit": ["text", "setText"],
                   "QComboBox": ["currentText", "setCurrentText"],
                   "QSpinBox": ["value", "setValue"],
                   "QCheckBox": ["isChecked", "setChecked"]}

    def __init__(self, QtWindow: QtWidgets, input_object=None):
        """
        Handles the GUI fields in a given QMainWindow object.

        Provides two useful functions for inputs:
            IOHandler.fields_to_inputs and IOHandler.inputs_to_fields: Write fields to the input object, and vice versa

        Inputs available as IOHandler.inputs

        :param QtWindow: The QMainWindow object
        """
        if input_object is None:
            class Inputs(object):
                pass
            self.inputs = Inputs()
        else:
            self.inputs = input_object

        _input_dict = self._connect_gui(self.inputs, QtWindow)

        self.fields_to_inputs, self.inputs_to_fields = self._get_connect_funcs(_input_dict)

    @staticmethod
    def _connect_gui(inputs: object, gui: QtWidgets.QMainWindow) \
            -> dict[str, list[Callable[[bool, str, Any], None], str, Any]]:

        """
        A function for connecting GUI input objects to other objects in the program.

        inputs will be given attributes corresponding to each Qt object in gui of the type:
            QLineEdit, QComboBox, QSpinBox, QCheckBox
            More to be added as I use them...

        The resulting attribute in inputs will have the same name as that object,
        which will be named as entered in QtDesigner, so put good names in there!

        Each key (which is name of object) in func_dict will then be loaded with a function, the object name,
        and the Qt object. The function allows values to be written from gui to inputs and vice versa.
        This function then returns that dict

        :param inputs: The object to have attributed added to it
        :param gui: the QtMainWindow object with the input objects
        :return: A dict of the form {"name": [function, "name", gui object], ...}
        """
        def _check_type(type_arg: str, item_arg: Any) -> bool:
            # return True if correct type and name matches attribute in inputs
            return False if type(item_arg).__name__ != type_arg else True

        def _connect_func(reverse: bool, key_arg: str, item_arg: Any, get_method: str, set_method: str) -> None:
            """
            A template connect function that will make anonymous functions that can be called later to
            easily set and load values to or from the GUI

            These functions are stored in func_dict

            :param reverse: when True, write inputs attributes to GUI fields. Otherwise, do the opposite
            :param key_arg: taken from gui.__dict__. The name of the parameter in inputs and gui
            :param item_arg: the Qt GUI Object.
                Its methods will be dynamically accessed with getattr(item_arg, xet_method)(*args)
            :param get_method: the name the Qt GUI's method that returns its value
            :param set_method: the name of the QT GUI's method that sets its value
            """
            if not reverse:
                # if writing to inputs, which is used for XML file creation, call the get attribute of the Qt object
                setattr(inputs, key_arg, getattr(item_arg, get_method)())
            else:
                try:
                    # else, call the set attribute of the Qt object
                    getattr(item_arg, set_method)(getattr(inputs, key_arg))
                except TypeError:
                    # configparser saves values like "True" as a string. If TypeError thrown, try eval()
                    getattr(item_arg, set_method)(eval(getattr(inputs, key_arg)))

        func_dict = {}

        # go through each of the attributes in the class instance
        for key, item in gui.__dict__.items():
            if key[0] == "_":  # don't access protected attributes
                continue

            def check_type(type_arg): return _check_type(type_arg, item)

            if check_type("QLineEdit"):  # look for attributes of the type 'QLineEdit'
                def connect_func(r: bool, k: str, i: Any): _connect_func(r, k, i, "text", "setText")
            elif check_type("QComboBox"):
                def connect_func(r: bool, k: str, i: Any): _connect_func(r, k, i, "currentText", "setCurrentText")
            elif check_type("QSpinBox"):
                def connect_func(r: bool, k: str, i: Any): _connect_func(r, k, i, "value", "setValue")
            elif check_type("QCheckBox"):
                def connect_func(r: bool, k: str, i: Any): _connect_func(r, k, i, "isChecked", "setChecked")
            else:
                continue  # don't assign fields[key] in this case

            # put into the fields dict so the local function can be accessed in other scopes
            func_dict[key] = [connect_func, key, item]
        return func_dict

    @staticmethod
    def _get_connect_funcs(input_field_dict: dict[str, list[Callable[[bool, str, Any], None], str, Any]]) \
            -> tuple[Callable[[], None], Callable[[], None]]:
        """
        Creates easy to use functions for reading and writing to GUI fields

        The first function writes field to values to the input object. The second does the reverse

        :param input_field_dict: dict returned from connect_gui
        :return: fields_to_inputs, inputs_to_fields
        """
        def fields_to_inputs(): [connect(False, key, item) for connect, key, item in input_field_dict.values()]
        def inputs_to_fields(): [connect(True, key, item) for connect, key, item in input_field_dict.values()]

        return fields_to_inputs, inputs_to_fields


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    window = load_ui_file("untitled.ui")

    io = IOHandler(window)
    io.fields_to_inputs()

    window.show()
    sys.exit(app.exec())
    pass
