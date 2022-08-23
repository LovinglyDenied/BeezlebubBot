import discord
from beartype import beartype
from beartype.typing import Optional


@beartype
def create_profile_embed(
        *,
        discord_name: str,
        join_date: str,
        last_active: Optional[str],
        chaster_name: Optional[str],
        owner: Optional[str],
        kinks_message: str,
        limits_message: str,
        avatar: str,
        derelict: bool
) -> discord.Embed:

    embed = discord.Embed(
        title=f"**{discord_name}**",
        colour=0xA343CB
    )
    embed.add_field(
        name="**First Appeared: **",
        value=join_date,
        inline=False
    )
    if last_active is not None:
        embed.add_field(
            name="**Last Active: **",
            value=last_active,
            inline=False
        )
    if chaster_name is not None:
        embed.add_field(
            name="**Chaster Name: **",
            value=chaster_name,
            inline=False
        )
    if owner is not None:
        embed.add_field(
            name="**Owner: **",
            value=owner,
            inline=False
        )
    embed.add_field(
        name="**Kinks Message: **",
        value=kinks_message,
        inline=False
    )
    embed.add_field(
        name="**Limits Message: **",
        value=limits_message,
        inline=False
    )
    embed.set_thumbnail(url=avatar)
    if derelict:
        embed.set_footer(text="Notice: this user is currently derelict.")

    return embed
