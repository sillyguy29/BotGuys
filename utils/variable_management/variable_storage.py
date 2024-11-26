"""
Contains the VariableStorage class.
"""

class VariableStorage:
    """
    Class for interfacing with a set of variables as referenced by their name
    """
    def __init__(self, variables=None):
        self.variables = {}
        #put the passed list of variables into a dictionary by their name
        for variable in [] if variables is None else variables:
            self.variables[variable.name] = variable

    def get_value_of(self,name):
        """
        Getter method for accessing the value of a variable in the storage by its name
        """
        return self.variables[name].get_value()

    def set_value_of(self,name, value):
        """
        Setter method for setting the value of avariable in the storage by its name
        """
        self.variables[name].set_value(value)

    def get_variable(self, name):
        """
        Getter method for directly accessing a variable in storage by its name
        """
        return self.variables[name]

    def get_variable_names(self):
        """
        Returns an iterable of contained variable keys
        """
        return self.variables.keys()
