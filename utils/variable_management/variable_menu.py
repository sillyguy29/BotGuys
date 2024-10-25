import discord

class VariableMenu:
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
        if value["type"] == "number":
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
        elif value["type"] == "select":
            select_menu = self.menu_view.children[value["index"]]
            select_menu.min_values = value["min_selected"]
            select_menu.max_values = value["max_selected"]
            select_menu.options = [
                discord.SelectOption(
                    label = x["label"],
                    value = x["value"],
                    default = x["value"] in value["value"]
                )
                for x in value["options"]
            ]
            async def set_value_from_select_menu(
                interaction,
                menu_in_question=select_menu,
                key=key
                ):
                self.game.preferences[key]["value"]=menu_in_question.values
                await interaction.response.send_message(
                    "response",
                    silent=True,
                    ephemeral=True,
                    delete_after=0
                )
            select_menu.callback = set_value_from_select_menu
            self.menu_view.children[value["index"]]=select_menu
        elif value["type"] == "boolean":
            #Similar to the select type but specifically for boolean values.
            #The naming could be better then just shoving the key name into
            #the label but it would require specifying it in the preferences dict.
            boolean_menu = self.menu_view.children[value["index"]]
            boolean_menu.min_values = 1
            boolean_menu.max_values = 1
            boolean_menu.options = [
                discord.SelectOption(
                    label = f"{key} Enabled",
                    value = "True",
                    default = value["value"]
                ),
                discord.SelectOption(
                    label = f"{key} Disabled",
                    value = "False",
                    default = not value["value"]
                )
            ]
            async def set_value_from_select_menu(
                interaction,
                menu_in_question=boolean_menu,
                key=key
                ):
                self.variable_storage.set_value(key, menu_in_question.values == "True")
                await interaction.response.send_message(
                    "response",
                    silent=True,
                    ephemeral=True,
                    delete_after=0
                )
            boolean_menu.callback = set_value_from_select_menu
        else:
            raise ValueError("Invalid preference type in game")

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
