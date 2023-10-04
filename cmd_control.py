import discord
import config


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

    response = input("\nShow global commands? y/N ")
    print("\nFetching local application commands...")
    if response == 'y' or response == 'Y':
        # Global commands
        commands = command_tree.get_commands()
    else:
        # Local commands
        response = input("\nWhich guild ID? (Enter nothing to use default): ")
        if not response.isdigit():
            # Default guild ID
            commands = await command_tree.get_commands(guild=discord.Object(config.GUILD_ID))
        else:
            # Custom guild ID
            commands = await command_tree.get_commands(guild=discord.Object(int(response)))

    print("\nLocal application commands:")
    n = 0
    for i in commands:
        print("[{2}] Name: {0} Desc: {1}".format(i.name, i.description, n))
        n += 1

    while True:
        response = input("\nEnter a number to view detailed info about the command, " 
                         + "'p' to re-print, and 'q' to go back: ")

        if response == 'q' or response == 'Q':
            return
        
        elif response == 'p' or response == 'P':
            n = 0
            print("\nLocal application commands:")
            for i in commands:
                print("[{2}] Name: {0} Desc: {1}".format(i.name, i.description, n))
                n += 1

        elif response.isdigit():
            response = int(response)
            if response >= len(commands):
                print("Invalid command nummber.")
                continue
            command = commands[response]
            print(parse_Command(command))


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

    response = input("\nFetch global commands? y/N ")
    print("\nFetching existing application commands...")
    if response == 'y' or response == 'Y':
        # Global commands
        commands = await command_tree.fetch_commands()
    else:
        # Local commands
        response = input("\nWhich guild ID? (Enter nothing to use default): ")
        if not response.isdigit():
            # Default guild ID
            commands = await command_tree.fetch_commands(guild=discord.Object(config.GUILD_ID))
        else:
            # Custom guild ID
            commands = await command_tree.fetch_commands(guild=discord.Object(int(response)))

    print("\nExisting application commands:")
    n = 0
    for i in commands:
        print("[{2}] Name: {0} Desc: {1}".format(i.name, i.description, n))
        n += 1

    while True:
        response = input("\nEnter a number to view detailed info about the command, " 
                         + "'p' to re-print, and 'q' to go back: ")

        if response == 'q' or response == 'Q':
            return
        
        elif response == 'p' or response == 'P':
            n = 0
            print("\nExisting application commands:")
            for i in commands:
                print("[{2}] Name: {0} Desc: {1}".format(i.name, i.description, n))
                n += 1

        elif response.isdigit():
            response = int(response)
            if response >= len(commands):
                print("Invalid command nummber.")
                continue
            command = commands[response]
            print(parse_AppCommand(command))


async def command_control(command_tree):
    while True:
        response = input("\nEnter 'l' to view local commands, 'e' to view the synced commands, "
                         + "'s' to sync commands, and 'r' to run the bot: ")
        
        if response == 'l' or response == 'L':
            await local_commands(command_tree)

        elif response == 'e' or response == 'E':
            await synced_commands(command_tree)

        elif response == 's' or response == 'S':
            inner_response = input("\nSync globally? y/N ")
            local_guild = True
            if inner_response == 'y' or inner_response == 'Y':
                local_guild = False

            inner_response = input("\nThis will overwrite existing commands."
                                   + " Are you sure? Y/n: ")
            if inner_response == 'n' or inner_response == 'N':
                print("Aborted.")
                continue

            if local_guild:
                # Sync to local guild
                response = input("\nWhich guild ID? (Enter nothing to use default): ")
                if not response.isdigit():
                    # Default
                    await command_tree.sync(guild=discord.Object(config.GUILD_ID))
                else:
                    await command_tree.sync(guild=discord.Object(int(response)))

            else:
                # Sync globally
                await command_tree.sync()
            continue
        
        elif response == 'r' or response == 'R':
            return