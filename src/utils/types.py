import discord
from beartype.typing import Union

MessageChannel = Union[
    discord.TextChannel,
    discord.DMChannel,
    discord.GroupChannel,
    discord.Thread,
]

DiscordMember = Union[
    discord.Member,
    discord.User
]
