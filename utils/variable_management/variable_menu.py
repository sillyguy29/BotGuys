"""
Contains the class for creating and managing a menu that interfaces with a particular variable
storage object.
"""
import discord
from utils.variable_management.variable_storage import VariableStorage

class VariableMenu:
    """
    Class for creating and managing a menu that interfaces with a particular variable storage
    object.
    """
    def __init__(self, variable_storage, variable_order=None):
        self.variable_storage = VariableStorage(None) if variable_storage is None else variable_storage 
        
        if variable_order is None:
            self.variable_layout = {
                key: {"order": index, "index": None}
                for index, key in
                enumerate(self.variable_storage.get_variable_names())
            } #TIL dict comprehensions are a thing, truly python is the most glorious of languages
        else:
            self.variable_layout = {
                key: {"order": index, "index": None}
                for index, key in
                enumerate(variable_order)
            }
        self.menu_view = discord.ui.View()

    def get_view(self):
        """
        Returns the view for displaying and editing variables.
        """
        return self.menu_view

    def add_ui_element(self, element):
        """
        Manually add a ui element, useful in the case where you want a button to do something that
        is not just modifying the value of a variable.
        """
        self.menu_view.add_item(element)

    def create_menu_item(self, key):
        """
        adds a placeholder menu item without contents and determines
        that items position within the view for future use
        """
        self.variable_layout[key]["index"]=len(self.menu_view.children)
        self.menu_view.add_item(self.variable_storage.get_variable(key).create_placeholder_ui_element())

    def generate_menu_item_contents(self, key):
        """
        generates the menu ui element for a given variable in preferences and inserts
        it into the view index it was assigned to
        """
        element = self.menu_view.children[self.variable_layout[key]["index"]]
        self.variable_storage.get_variable(key).assign_ui_element_contents(element, self.menu_view)

    def add_menu_items(self):
        """
        Prepares a variable menu view for display by
        adding the ui elements needed to edit the variables in variable storage
        and then generating their contents.
        """
        ordered_by_layout = [
            x[0]
            for x in
            sorted(
                [
                    (dKey,value["order"])
                    for dKey,value in
                    self.variable_layout.items()
                ],
                key = lambda x: x[1])
        ]
        for key in ordered_by_layout:
            self.create_menu_item(key)

        for key in self.variable_storage.get_variable_names():
            self.generate_menu_item_contents(key)
