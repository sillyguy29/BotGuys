import discord
import config

def print_commands(commands):
    n = 0
    for i in commands:
        print("[{2}] Name: {0} Desc: {1}".format(i.name, i.description, n))
        n += 1


def restore_commands(command_tree, commands):
    # need to ensure no conflicts
    command_tree.clear_commands(guild=None)
    for i in commands:
        command_tree.add_command(i)


async def local_commands(command_tree):
    """
    Show details for commands loaded from local code. These commands are of type
    discord.app_commands.Command. 
    """
    # Pretty print functions used below
    def get_params_str(params):
        r_string = ""
        for i in params:
            r_string = "\t" + i.name + "\n"
        return r_string
    
    def parse_Command(command):
        details = ("Detailed info for command [{}]: \n".format(command.name)
        + "Desc: {}\n".format(command.description)
        + "Guild Only: {}\n".format(command.guild_only)
        + "Parent: {}\n".format(command.parent)
        + "Usage Permissions Requirement Integer: ")
        if command.default_permissions is None:
            details = details + "None (Likely Default)\n"
        else:
            details = details + str(command.value) + "\n"
        details = details + ("Parameters:\n{}".format(get_params_str(command.parameters))
        + "Extra Data: {}".format(command.extras))
        return details
    

    print("\nFetching local application commands...")
    commands = command_tree.get_commands()
    print("\nLocal commands, loaded from the code on your machine:")
    print_commands(commands)

    while True:
        response = input("\nEnter a number to view detailed info and/or remove the command, " 
                         + "'x' to remove all commands, 'p' to re-print, and 'q' to go back: ")

        if response == 'q' or response == 'Q':
            return
        
        elif response == 'p' or response == 'P':
            print("\nFetching local application commands...")
            commands = command_tree.get_commands()
            print("\nLocal commands, loaded from the code on your machine:")
            print_commands(commands)

        elif response == 'x' or response == 'X':
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
            print(parse_Command(command))

            response = input("\nRemove command? y/N: ")
            if response == "y" or response == "Y":
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
    # pretty print function used below
    def parse_AppCommand(command):
        details = ("Detailed info for command [{}]: \n".format(command.name)
        + "Desc: {}\n".format(command.description)
        + "Command ID: {}\n".format(command.id)
        + "Guild ID: {}\n".format(command.guild_id)
        + "Application ID: {}\n".format(command.application_id)
        + "DM Permission: {}\n".format(command.dm_permission)
        + "Usage Permissions Requirement Integer: ")
        if command.default_member_permissions is None:
            return details + "None (Likely Default)"
        else:
            return details + str(command.value)
        

    response = input("\nFetch global commands? y/N: ")
    if response == 'y' or response == 'Y':
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

        if response == 'q' or response == 'Q':
            return
        
        elif response == 'p' or response == 'P':
            print_commands(command)

        elif response.isdigit():
            response = int(response)
            if response >= len(commands):
                print("Invalid command nummber.")
                continue
            command = commands[response]
            print(parse_AppCommand(command))

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
        
        if response == 'l' or response == 'L':
            await local_commands(command_tree)

        elif response == 'v' or response == 'V':
            await synced_commands(command_tree)

        elif response == 's' or response == 'S':
            inner_response = input("\nSync globally? y/N: ")
            local_guild = True
            if inner_response == 'y' or inner_response == 'Y':
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
                if inner_response == 'n' or inner_response == 'N':
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

            else:
                # Sync globally
                inner_response = input("\nThis will overwrite existing global commands. It "
                                        + "may also take up to an hour to register. "
                                        + "Are you sure? Y/n: ")
                if inner_response == 'n' or inner_response == 'N':
                    print("Aborted.")
                    continue
                await command_tree.sync()
                continue

        elif response == 'e' or response == 'E':
            restore_commands(command_tree, local_command_list)
        
        elif response == 'r' or response == 'R':
            # Ensure that all commands are still available on the backend, even if they
            # can't be called
            restore_commands(command_tree, local_command_list)
            return
        
        else:
            print("Unrecognized command.")