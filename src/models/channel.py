from __future__ import annotations

import discord
from discord import abc
from beartype import beartype
from beartype.abby import is_bearable
from beartype.typing import Union, Optional

from utils import mention_to_id, MessageChannel
from .context import ModelContext


class MainTextChannel:
    """A wrapper class for a guild text channel"""

    @beartype
    def __init__(self, *, context: ModelContext):
        self.context = context

    @classmethod
    @beartype
    async def from_mention(
        cls,
        mention_string: str,
        *,
        context: ModelContext,
        **kwargs
    ) -> MainTextChannel:
        """Creates a new instance from a mention string
        responds to context and trows ManagedCommandError of not possible"""
        try:
            discord_id = mention_to_id(mention_string)
        except ValueError:
            await context.exit(
                f"{mention_string} is not recognised as a Channel. Are you sure you used either a mention or a discord channel ID?",
            )
        return await cls._init(discord_id=discord_id, context=context, **kwargs)

    @classmethod
    @beartype
    async def _init(
            cls,
            *,
            discord_id: int,
            context: ModelContext
    ) -> MainTextChannel:
        """Initialses from an int ID
        Only initialises via ID to make sure the channel is in cashe
        Raises ValueError if initialised with incorrect options
        Responds to context and raises ManagedCommandError for "runtime" erros"""

        instance = cls(context=context)

        channel: Optional[MessageChannel] = context.bot.get_channel(
            int(discord_id))

        if channel is None:
            try:
                channel = await context.bot.fetch_channel(int(discord_id))
                instance.fetched = True
            except (discord.InvalidData, discord.NotFound, discord.Forbidden) as error:
                await context.exit(
                    f"Could not find channel {discord_id}, {error}"
                )

        if not is_bearable(channel, MessageChannel):
            await context.exit(
                f"{channel.mention} is not a valid Guild TextChannel"
            )

        instance.discord: MessageChannel = channel

        return instance


@beartype
async def create_main_text_channel(*args, **kwargs) -> MainTextChannel:
    return await MainTextChannel._init(*args, **kwargs)
