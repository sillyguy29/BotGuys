"""
Contains the class for creating and managing a menu that interfaces with a particular variable
storage object.
"""
import discord

class VariableMenu:
    """
    Class for creating and managing a menu that interfaces with a particular variable storage
    object.
    """
    def __init__(self, variable_storage):
        self.variable_storage = variable_storage
        self.variable_layout = {
            key: {"order": index, "index": None}
            for index, key in
            enumerate(self.variable_storage.get_variable_names())
        } #TIL dict comprhensions are a thing, truly python is the most glorious of languages
        self.menu_view = discord.ui.View()

    def create_menu_item(self, key):
        """
        adds a placeholder menu item without contents and determines
        that items position within the view for future use
        """
        self.variable_layout[key]["index"]=len(self.menu_view.children)
        self.menu_view.add_item(self.variable_storage[key].create_placeholder_ui_element())

    def generate_menu_item_contents(self, key):
        """
        generates the menu ui element for a given variable in preferences and inserts
        it into the view index it was assigned to
        """
        element = self.menu_view.children[self.variable_storage.variable_layout["index"]]
        self.variable_storage[key].assign_ui_element_contents(element, self.menu_view)

    def add_menu_items(self):
        """
        Adds the ui elements needed to change the preferences of a managers game to a view
        """
        ordered_by_layout = [
            x[0]
            for x in
            sorted(
                [
                    (dKey,value["order"])
                    for dKey,value in
                    self.variable_layout
                ],
                key = lambda x: x[1])
        ]
        for key in ordered_by_layout:
            self.create_menu_item(key)

        for key in self.variable_storage.get_variable_names:
            self.generate_menu_item_contents(key)
