"""
Module storing the different types of variable classes and their helper classes.
"""

#TODO implement localization features for integer variables
#TODO implement localization features for boolean variables

import discord

class Variable:
    """
    The base variable class, only contains a name as other types of variable
    would not use value variables of the same type and strict type sensibilities
    require that variables be defined such that they are the same type usually.
    """
    def __init__(self,name):
        self.name = name

class IntegerVariable(Variable):
    """
    An integer variable class, stores a variable and includes the defined methods to interact with
    a variable or setup a menu involving it. Also stores the restrictions on the variable.
    Range restrictions are inclusive for the value, e.g. min<=value<=max
    Intended usage is:
    `IntegerVariable("MyVariable", 40)`
    `IntegerVariable("MyVariable", -20, range_min=-100)`
    `IntegerVariable("MyVariable", 40)`
    Unintended usage is:
    `IntegerVariable("MyVariable", 40.0)`
    `IntegerVariable("MyVariable", -30)`
    `IntegerVariable("MyVariable", -30, range_min=200)`
    `IntegerVariable("MyVariable", -30, range_min=-50, range_max=-40)`
    """
    def __init__(self, name, default_value=0, range_min=0, range_max=None):
        super().__init__(name)
        self.value = int(default_value)
        self.range_min = range_min
        self.range_max = range_max

    def set_value(self,value):
        """
        Setter method
        Will not update preferences_view on change
        Sorry, my java instincts came back and the hole is too deep to fill in now.
        """
        self.value = int(value)

    def get_value(self):
        """
        Getter method
        """
        return self.value

    def create_placeholder_ui_element(self):
        """
        Creates a placeholder UI element suitable for being used as an interface to change 
        an integer variable's value. (A button element at the moment)
        This is used when initializing the view's children before setting this placeholder's
        internal values to non-placeholder ones. Wholesale replacing the object with a different
        one in the view list does not work so one needs to swap out the elements labels and such.
        Because this happens immediately upon showing the menu for the first time setting the
        initial values to the correct values is unnecessary. Hence the values being placeholders.
        """
        generated_button = discord.ui.Button(label="Placeholder")
        return generated_button

    def assign_ui_element_contents(self, button, view_present_in):
        """
        This will update the values of a suitable UI element to make it an interface to change this
        integer variable's value as of calling this method. I.e. if it updates the text on a button
        that has the value of this variable on it if it has changed.
        """
        button.label=f"{self.name} is {self.value}"
        generated_modal = discord.ui.Modal(
            title=self.name
        )
        generated_modal.add_item(discord.ui.TextInput(
            label=self.name,
            placeholder="Enter a number...",
            default=str(self.value),
            min_length=len(str(self.range_min)),
            max_length=len(str(self.range_max))
        ))
        async def set_value_from_modal(
            interaction, modal_in_question=generated_modal,
            key=self.name
            ):
            self.value = int(modal_in_question.children[0].value)
            self.assign_ui_element_contents(button, view_present_in)
            modal_in_question.stop()
            await interaction.response.edit_message(view=view_present_in)
        async def interaction_check_for_modal(
            interaction,
            modal_in_question=generated_modal,
            key=self.name
            ):
            try:
                val = int(modal_in_question.children[0].value)
                if not (
                    self.range_min <= val and
                    self.range_max >= val
                    ):
                    return False
            except ValueError:
                return False
            return True
        generated_modal.interaction_check = interaction_check_for_modal
        generated_modal.on_submit = set_value_from_modal
        async def bring_up_modal(
            interaction,
            modal_to_use=generated_modal
            ):
            await interaction.response.send_modal(modal_to_use)
        button.callback = bring_up_modal

class OptionRepresentation():
    """
    A helper class for the OptionVariable class, stores what the name of an option
    should be presented as and what the internal representation is.
    This would help if we ever added a flavor text localization system and does help
    with preventing internal value names from being subject to grammatical rules when
    unnecessary. 
    """
    def __init__(self, presentation_string, internal_value):
        self.presentation_string = presentation_string
        self.internal_value = internal_value

class OptionVariable(Variable):
    """
    An option variable class, i.e. a variable that stores a list of options selected from a
    list of available options.
    default_value holds a list of internal values
    options holds a list of OptionRepresentation
    Options should be non empty, if it is not, it will be made so that it is.
    """
    def __init__(
        self,
        name,
        default_value,
        min_selected=1,
        max_selected=1,
        options=None
        ):
        super().__init__(name)
        if options is None or options == []:
            options=[OptionRepresentation("Placeholder value", "placeholder_value")]
        self.value = default_value
        self.min_selected = min_selected
        self.max_selected = max_selected
        self.options = options

    def set_value(self,value):
        """
        Setter method
        """
        self.value = list(value)

    def get_value(self):
        """
        Getter method
        """
        return self.value

    def create_placeholder_ui_element(self):
        """
        Creates a placeholder UI element suitable for being used as an interface to change 
        an option variable's value. (A select menu at the moment)
        """
        generated_select_menu = discord.ui.Select(
            options=[
                discord.SelectOption(label="Placeholder")
            ]
        )
        return generated_select_menu

    def assign_ui_element_contents(self, select_menu, view_present_in):
        """
        Assigns the values to a suitable UI element to make it an interface to change this select
        variable's value.
        """
        select_menu.min_values = self.min_selected
        select_menu.max_values = self.max_selected
        select_menu.options = [
            discord.SelectOption(
                label = x.presentation_string,
                value = x.internal_value,
                default = x.internal_value in self.value
            )
            for x in self.options
        ]
        async def set_value_from_select_menu(
            interaction,
            menu_in_question=select_menu,
            key=self.name
            ):
            self.value=menu_in_question.values
            self.assign_ui_element_contents(select_menu, view_present_in)
            await interaction.response.edit_message(view=view_present_in)
        select_menu.callback = set_value_from_select_menu

class BooleanVariable(OptionVariable):
    """
    A Boolean variable class, while its value is closer to an integer in nature, the currently
    selected interface for this variable is a select menu, as such it inherits from the
    OptionVariable in order to reuse its UI code.
    """
    def __init__(self, name, default_value):
        super().__init__(
            name,
            default_value=[
                default_value
            ],
            options=[
                OptionRepresentation(f"{name} Enabled", True),
                OptionRepresentation(f"{name} Disabled", False)
            ]
        )
        self.value = default_value

    def assign_ui_element_contents(self, select_menu, view_present_in):
        """
        Assigns the values to a suitable UI element to make it an interface to change this boolean
        variable's value.
        """
        select_menu.min_values = self.min_selected
        select_menu.max_values = self.max_selected
        select_menu.options = [
            discord.SelectOption(
                label = x.presentation_string,
                value = x.internal_value,
                default = x.internal_value in [self.value]
            )
            for x in self.options
        ]
        async def set_value_from_select_menu(
            interaction,
            menu_in_question=select_menu,
            key=self.name
            ):
            self.value=bool(menu_in_question.values[0])
            self.assign_ui_element_contents(select_menu, view_present_in)
            await interaction.response.edit_message(view=view_present_in)
        select_menu.callback = set_value_from_select_menu

    def set_value(self,value):
        """
        Setter method
        """
        self.value = value

    def get_value(self):
        """
        Getter method
        """
        return self.value
