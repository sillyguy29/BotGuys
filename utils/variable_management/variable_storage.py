"""
Contains the VariableStorage class.
"""

class VariableStorage:
    """
    Class for interfacing with a set of variables as referenced by their name
    """
    def __init__(self, variables=None):
        if variables is None:
            self.variables = {}

    def get_value_of(self,name):
        """
        Getter method for accessing a variable in the storage by its name
        """
        return self.variables[name].getValue()

    def set_value_of(self,name, value):
        """
        Setter method for setting a variable in the storage by its name
        """
        self.variables[name].setValue(value)

    def get_variable_names(self):
        """
        Returns an iterable of contained variable keys
        """
        return self.variables.keys()
