"""Terminal menu for managing slash commands

Contains all the logic needed to sync slash commands.
"""
import discord
import configs.config as config

def print_commands(commands):
    """
    Quick loop that prints all commands in a list.
    """
    n = 0
    for i in commands:
        print(f"[{n}] Name: {i.name} Desc: {i.description}")
        n += 1


def restore_commands(command_tree, commands):
    """
    Clears the commands in the command tree and replaces it with the
    list of commands provided.
    """
    # need to ensure no conflicts
    command_tree.clear_commands(guild=None)
    for i in commands:
        command_tree.add_command(i)


async def local_commands(command_tree):
    """
    Show details for commands loaded from local code. These commands are of type
    discord.app_commands.Command. 
    """
    def get_params_str(params):
        """
        Take a parameter and turn it into a string
        """
        r_string = ""
        for i in params:
            r_string = "\t" + i.name + "\n"
        return r_string

    def parse_command(command):
        """
        Pretty print a Discord.Command
        """
        details = (f"Detailed info for command [{command.name}]: \n"
        + f"Desc: {command.description}\n"
        + f"Guild Only: {command.guild_only}\n"
        + f"Parent: {command.parent}\n"
        + "Usage Permissions Requirement Integer: ")
        if command.default_permissions is None:
            details = details + "None (Likely Default)\n"
        else:
            details = details + str(command.value) + "\n"
        details = details + (f"Parameters:\n{get_params_str(command.parameters)}"
        + f"Extra Data: {command.extras}")
        return details


    print("\nFetching local application commands...")
    commands = command_tree.get_commands()
    print("\nLocal commands, loaded from the code on your machine:")
    print_commands(commands)

    while True:
        response = input("\nEnter a number to view detailed info and/or remove the command, "
                         + "'x' to remove all commands, 'p' to re-print, and 'q' to go back: ")

        if response in {'q', 'Q'}:
            return

        if response in {'p', 'P'}:
            print("\nFetching local application commands...")
            commands = command_tree.get_commands()
            print("\nLocal commands, loaded from the code on your machine:")
            print_commands(commands)

        elif response in {'x', 'X'}:
            print("\nClearing the local command tree...")
            command_tree.clear_commands(guild=None)
            print("\nCommand tree cleared.")
            return

        elif response.isdigit():
            response = int(response)
            if response >= len(commands):
                print("\nInvalid command nummber.")
                continue
            command = commands[response]
            print(parse_command(command))

            response = input("\nRemove command? y/N: ")
            if response in {'y', 'Y'}:
                command_tree.remove_command(command.name)
                print("\nCommand removed.")
                print("\nFetching local application commands...")
                commands = command_tree.get_commands()
                print("\nLocal commands, loaded from the code on your machine:")
                print_commands(commands)

        else:
            print("Unrecognized command.")



async def synced_commands(command_tree):
    """
    Show details for commands loaded from local code. These commands are of type
    discord.app_commands.AppCommand. 
    """
    def parse_app_command(command):
        """
        Pretty print a Discord.AppCommand
        """
        details = (f"Detailed info for command [{command.name}]: \n"
        + f"Desc: {command.description}\n"
        + f"Command ID: {command.id}\n"
        + f"Guild ID: {command.guild_id}\n"
        + f"Application ID: {command.application_id}\n"
        + f"DM Permission: {command.dm_permission}\n"
        + "Usage Permissions Requirement Integer: ")
        if command.default_member_permissions is None:
            return details + "None (Likely Default)"
        return details + str(command.value)


    response = input("\nFetch global commands? y/N: ")
    if response in {'y', 'Y'}:
        # Global commands
        print("\nFetching existing global application commands...")
        commands = await command_tree.fetch_commands()
    else:
        # Local commands
        response = input("\nWhich guild ID do you want to fetch the commands from? "
                        + "(Enter nothing to use default): ")
        if not response.isdigit():
            print("\nFetching existing commands from default guild...")
            commands = await command_tree.fetch_commands(guild=discord.Object(config.GUILD_ID))
        else:
            print("\nFetching existing commands from guild " + response + "...")
            commands = await command_tree.fetch_commands(guild=discord.Object(int(response)))

    print("\nExisting application commands:")
    print_commands(commands)

    while True:
        response = input("\nEnter a number to view detailed info about the command, "
                         + "'p' to re-print, and 'q' to go back: ")

        if response in {'q', 'Q'}:
            return

        if response in {'p', 'P'}:
            print_commands(commands)

        elif response.isdigit():
            response = int(response)
            if response >= len(commands):
                print("Invalid command number.")
                continue
            command = commands[response]
            print(parse_app_command(command))

        else:
            print("Unrecognized command.")


async def command_control(command_tree):
    """
    Input loop designed to handle syncing of commands.
    """
    # save a copy of existing commands
    local_command_list = command_tree.get_commands()
    while True:
        response = input("\nEnter 'l' to view local commands, 'v' to view the synced commands, "
                         + "'s' to sync commands, 'e' to restore removed local commands, and 'r' "
                         + "to run the bot: ")

        if response in {'l', 'L'}:
            await local_commands(command_tree)

        elif response in {'v', 'V'}:
            await synced_commands(command_tree)

        elif response in {'s', 'S'}:
            inner_response = input("\nSync globally? y/N: ")
            local_guild = True
            if inner_response in {'y', 'Y'}:
                local_guild = False

            if local_guild:
                # Sync to local guild
                response = input("\nWhich guild ID? (Enter nothing to use default): ")

                if response.isdigit():
                    response = int(response)
                else:
                    response = config.GUILD_ID

                inner_response = input("\nThis will overwrite existing commands for guild "
                                        + str(response) + ". Are you sure? Y/n: ")
                if inner_response in {'n', 'N'}:
                    print("Aborted.")
                    continue

                # Copy the global commands to a guild, sync those commands, clean up
                command_tree.copy_global_to(guild=discord.Object(response))
                await command_tree.sync(guild=discord.Object(response))
                # When a guild command is not found (which it won't, because this is clearing it)
                # it will fallback on a version of the command not associated with any guild.
                # This will always exist since we restore before running
                command_tree.clear_commands(guild=discord.Object(response))
                continue

            # Sync globally
            inner_response = input("\nThis will overwrite existing global commands. It "
                                    + "may also take up to an hour to register. "
                                    + "Are you sure? Y/n: ")
            if inner_response in {'n', 'N'}:
                print("Aborted.")
                continue
            await command_tree.sync()
            continue

        elif response in {'e', 'E'}:
            restore_commands(command_tree, local_command_list)

        elif response in {'r', 'R'}:
            # Ensure that all commands are still available on the backend, even if they
            # can't be called
            restore_commands(command_tree, local_command_list)
            return

        else:
            print("Unrecognized command.")
