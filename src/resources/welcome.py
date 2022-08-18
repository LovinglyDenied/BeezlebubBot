import discord


def create_welcome_embed(
        title: str,
        member_join: str,
        member_avatar: str,
        member_name: str
) -> discord.Embed:

    embed = discord.Embed(
        title=title,
        description=member_name,
        colour=0xA343CB
    )
    embed.add_field(
        name="**Joined Discord: **",
        value=member_join,
        inline=False
    )
    embed.set_thumbnail(url=member_avatar)

    return embed


# This has to be done with a function instead of by subclassing View
# The @button declarator does not support links
def create_welcome_view(
        rules_link: str,
        rules_message: str,
        roles_link: str,
        roles_message: str,
        guide_link: str,
        guide_message: str,
) -> discord.ui.View:

    rules_button: discord.ui.Button = discord.ui.Button(
        label=rules_message,
        style=discord.ButtonStyle.link,
        url=rules_link
    )

    roles_button: discord.ui.Button = discord.ui.Button(
        label=roles_message,
        style=discord.ButtonStyle.link,
        url=roles_link
    )
    guide_button: discord.ui.Button = discord.ui.Button(
        label=guide_message,
        style=discord.ButtonStyle.link,
        url=guide_link
    )

    return discord.ui.View(rules_button, roles_button, guide_button)
