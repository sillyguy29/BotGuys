import discord

class Variable:
    def __init__(self,name):
        self.name = name

class IntegerVariable(Variable):
    def __init__(self, name, default_value=0, range_min=0, range_max=None):
        super().__init__(name)
        self.value = int(default_value)
        self.range_min = 0
        self.range_max = 0

    def set_value(self,value):
        self.value = int(value)

    def get_value(self):
        return self.value

    def create_placeholder_ui_element(self):
        generated_button = discord.ui.Button(label="Placeholder")
        return generated_button

    def assign_ui_element_contents(self, button):
        button=self.menu_view.children[value["index"]]
        button.label=f"{key} is {value['value']}"
        generated_modal = discord.ui.Modal(
            title=key
        )
        generated_modal.add_item(discord.ui.TextInput(
            label=key,
            placeholder="Enter a number...",
            default=str(value["value"]),
            min_length=len(str(value["min"])),
            max_length=len(str(value["max"]))
        ))
        async def set_value_from_modal(
            interaction, modal_in_question=generated_modal,
            key=key
            ):
            self.game.preferences[key]["value"] = int(modal_in_question.children[0].value)
            self.generate_menu_item_contents(key, self.game.preferences[key])
            modal_in_question.stop()
            await interaction.response.edit_message(view=self.menu_view)
        async def interaction_check_for_modal(
            interaction,
            modal_in_question=generated_modal,
            key=key
            ):
            try:
                val = int(modal_in_question.children[0].value)
                if not (
                    self.game.preferences[key]["min"] < val and
                    self.game.preferences[key]["max"] > val
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
    def __init__(self, presentation_string, internal_value):
        self.presentation_string = presentation_string,
        self.internal_value = internal_value

class OptionVariable(Variable):
    def __init__(
        self,
        name,
        default_value,
        min_selected=1,
        max_selected=1,
        options=[OptionRepresentation("Placeholder value", "placeholder_value")]
        ):
        super().__init__(name)
        self.value = default_value
        self.min_selected = min_selected
        self.max_selected = max_selected
        self.options = options

    def set_value(self,value):
        self.value = list(value)

    def get_value(self):
        return self.value

    def create_placeholder_ui_element(self):
        generated_select_menu = discord.ui.Select(
            options=[
                discord.SelectOption(label="Placeholder")
            ]
        )
        return generated_select_menu


class BooleanVariable(OptionVariable):
    def __init__(self, name, default_value):
        super().__init__(
            name,
            default_value=[
                OptionRepresentation("Enabled", True)
                if default_value else
                OptionRepresentation("Disabled", False)
            ],
            options=[
                OptionRepresentation("Enabled", True), 
                OptionRepresentation("Disabled", False)
            ]
        )
