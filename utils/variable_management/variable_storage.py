class VariableStorage:
    def __init__(self, variables={}):
        self.variables = variables

    def getValueOf(self,name):
        return self.variables[name].getValue()

    def setValueOf(self,name, value):
        self.variables[name].setValue(value)

    def get_variable_names(self):
        return self.variables.keys()
