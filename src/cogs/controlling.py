import asyncio
import logging
from typing import Optional, List

import discord
from discord.commands import SlashCommandGroup, Option

from database.user import DBUser
from models import Player, ModelACTX
from resources import create_controlling_request_embed, create_controlling_request_view
from .base import BaseCog


class Controlling(BaseCog):
    control = SlashCommandGroup(
        "control", "Manage relations, and who is controlled by who")

    def __init__(self, bot):
        self.bot = bot

    async def send_control_request(
        self,
        instantiator: Player,
        target: Player
    ):
        dmchannel = await target.get_dm()
        embed = create_controlling_request_embed(
            instantiator_name=str(instantiator.discord),
            instantiator_picture=str(instantiator.discord.display_avatar)
        )
        view = create_controlling_request_view(
            instantiator=instantiator,
            target=target,
            bot=self.bot
        )
        await dmchannel.send(view=view, embed=embed)

    @control.command(
        name="request",
        description="request to control the user")
    async def request(
        self,
        ctx: discord.ApplicationContext,
        player_mention: Option(
            input_type=discord.User,
            name="user",
            description="the user you want to own."
        )
    ):
        instantiator: Player = await Player.from_ctx(ctx, get_db=True)
        target: Player = await Player.from_mention(
            player_mention,
            context=ModelACTX(ctx),
            get_discord=True,
            get_db=True,
            as_user=ctx.user.id
        )
        if target == instantiator:
            await ctx.respond("You cannot send a control request to yourself", ephemeral=True)
            return
        elif target.is_owned_by(instantiator):
            await ctx.respond(f"You already control {target.discord.mention}.", ephemeral=True)
            return
        elif target.has_owner:
            await ctx.respond(f"{target.discord.mention} already has an owner.", ephemeral=True)
            return
        elif target.db.allow_requests == False:
            await ctx.respond(f"{target.discord.mention} does not allow requests.", ephemeral=True)
            return

        try:
            await self.send_control_request(instantiator, target)
            await ctx.respond(f"Sent a controll request to {target.discord.mention}", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond(f"Cannot send a request: The DM settings of {target.discord.mention} do not allow to send the message.")

    @control.command(
        name="trust",
        description="Trusts your current owner")
    async def trust(
        self,
        ctx: discord.ApplicationContext
    ):
        player: Player = await Player.from_ctx(ctx, get_db=True)

        if not player.has_owner:
            await ctx.respond(f"You are currently not owned by anyone", ephemeral=True)
            return
        if player.db.trusts == True:
            await ctx.respond(f"You had already trusted your owner!", ephemeral=True)
            return

        owner: Optional[Player] = await player.get_owner(get_discord=True)

        DBUser.change_setting(
            db_id=player.db._id,
            setting="trusts",
            value=True
        )
        await owner.notify(f"{player.discord.mention} now trusts you!")
        await ctx.respond(f"You have now trusted your owner, {owner.discord.mention}", ephemeral=True)

    @control.command(
        name="free",
        description="Free the target player from your controll.")
    async def free(
        self,
        ctx: discord.ApplicationContext,
        player_mention: Option(
            input_type=discord.User,
            name="user",
            description="the user you want to own."
        )
    ):
        instantiator: Player = await Player.from_ctx(ctx, get_db=True)
        target: Player = await Player.from_mention(
            player_mention,
            context=ModelACTX(ctx),
            get_db=True
        )
        if target == instantiator:
            await ctx.respond("You cannot free yourself", ephemeral=True)
            return
        elif not target.is_owned_by(instantiator):
            await ctx.respond(f"You do not control {target.discord.mention}.", ephemeral=True)
            return
        target._set_owner(target, trusts=False)
        await target.notify(f"You are no longer owned by {instantiator.discord.mention}. They freed you")

        await ctx.respond(f"You freed {target.discord.mention}", ephemeral=True)

    @control.command(
        name="update",
        description="Update who owns you. Resets your owner if they're derelict.")
    async def update(
        self,
        ctx: discord.ApplicationContext
    ):
        player: Player = await Player.from_ctx(ctx, get_db=True)
        owner: Optional[Player] = await player.update_owner()
        if owner is None:
            await ctx.respond(f"Updated your owner. You currently do not have one.", ephemeral=True)
        else:
            await ctx.respond(f"Updated your owner. Your owner is {owner.discord.mention}", ephemeral=True)

    @control.command(
        name="owner",
        description="Shows who owns you.")
    async def owner(
        self,
        ctx: discord.ApplicationContext
    ):
        player: Player = await Player.from_ctx(ctx, get_db=True)
        owner: Player = await player.get_owner(get_discord=True)
        if owner == player:
            await ctx.respond(f"You are currently not owned by anyone", ephemeral=True)
        else:
            if player.db.trusts:
                trusts: str = "You have trusted them."
            else:
                trusts: str = "You have not trusted them."
            await ctx.respond(f"You are owned by {owner.discord.mention}, ID: {owner.discord.id}, {trusts}", ephemeral=True)

    @control.command(
        name="owned",
        description="Show who you own")
    async def owner(
        self,
        ctx: discord.ApplicationContext
    ):
        player: Player = await Player.from_ctx(ctx, get_db=True)
        owned: Optional[List[Player]] = await player.get_owned()

        if owned is None:
            await ctx.respond(f"You currently do not own anyone", ephemeral=True)
            return

        owned_names: List[str] = []
        for controlled in owned:
            if controlled.db.trusts:
                owned_names.append(
                    f"\t- {controlled.discord.mention}.\tID: {controlled.discord.id}\tThey have trusted you.")
            else:
                owned_names.append(
                    f"\t- {controlled.discord.mention}.\tID: {controlled.discord.id}\tThey have not trusted you.")
        names: str = "\n".join(owned_names)
        await ctx.respond(f"You currently own the following player(s):\n\n {names}", ephemeral=True)

    @control.command(
        name="allow_requests",
        description="Manage whether or not you allow control requests")
    async def allow_requests(
        self,
        ctx: discord.ApplicationContext,
        value: Option(bool)
    ):
        DBUser.change_setting(
            discord_id=ctx.user.id,
            setting="allow_requests",
            value=bool(value)
        )
        await ctx.respond(f"Changed `allow_requestss` setting to `{value}`", ephemeral=True)

    def cog_unload(self):
        logging.info("Cog Controlling unloaded")


def setup(bot):
    bot.add_cog(Controlling(bot))
    logging.info("Cog Controlling loaded")
