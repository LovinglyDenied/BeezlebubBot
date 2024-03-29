import discord
import discord.ui as ui
from beartype import beartype

from models import Player, ModelVCTX
from .base import BaseView


class ControllingRequestView(BaseView):
    @beartype
    def __init__(self, *, instantiator: Player, target: Player, bot: discord.ext.commands.Bot):
        super().__init__(timeout=60)
        self.instantiator: Player = instantiator
        self.target: Player = target
        self.bot: discord.ext.commands.Bot = bot
        self.accepted = False

    def interact_hook(self):
        context = ModelVCTX(message=self.message, bot=self.bot)
        self.target.context = context
        self.instantiator.context = context

    @ui.button(label="Accept")
    async def accept_button_callback(self, button: ui.Button, interaction: discord.Interaction):
        self.interact_hook()
        await self.target.set_owner(self.instantiator, trusts=False)
        self.accepted = True
        button.label = f"Accepted request from {self.instantiator.discord}"
        button.style = discord.ButtonStyle.green
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        self.stop()

    @ui.button(label="Accept and trust")
    async def trust_button_callback(self, button: ui.Button, interaction: discord.Interaction):
        self.interact_hook()
        await self.target.set_owner(self.instantiator, trusts=True)
        self.accepted = True
        button.label = f"Accepted request and trusted {self.instantiator.discord}"
        button.style = discord.ButtonStyle.green
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        self.stop()

    @ui.button(label="Decline")
    async def decline_button_callback(self, button: ui.Button, interaction: discord.Interaction):
        self.interact_hook()
        button.label = "Declined request. Deleting message"
        button.style = discord.ButtonStyle.red
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        await self.message.delete(delay=5)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target.discord.id:
            await interaction.response.send_message(
                f"This request was send to {self.target.discord.mention}, not you.",
                ephemeral=True)
            return False
        else:
            return await super().interaction_check(interaction)

    async def on_timeout(self):
        if not self.accepted:
            embed = create_controlling_request_timed_out_embed(
                instantiator_name=str(self.instantiator.discord),
                instantiator_picture=str(self.instantiator.discord.display_avatar)
            )
            await self.message.edit(
                embed=embed,
                view=None
            )


@beartype
def create_controlling_request_view(**kwargs) -> BaseView:
    return ControllingRequestView(**kwargs)


@beartype
def create_controlling_request_timed_out_embed(
        *,
        instantiator_name: str,
        instantiator_picture: str
) -> discord.Embed:
    embed = discord.Embed(
        title=f"**{instantiator_name} wanted to controll you.**",
        colour=0xA343CB
    )
    embed.add_field(
        name="This control request timed out.",
        value="If you want them to controll you, please ask them to send a new request.",
        inline=False
    )
    embed.add_field(
        name="If this was unwarranted, you can block them.",
        value="Do this with `/block add`",
        inline=False
    )
    embed.add_field(
        name="You can disable all control requests",
        value="Do this with `/control allow_requests false`",
        inline=False
    )
    embed.set_thumbnail(url=instantiator_picture)

    return embed


@beartype
def create_controlling_request_embed(
        *,
        instantiator_name: str,
        instantiator_picture: str
) -> discord.Embed:

    embed = discord.Embed(
        title=f"**{instantiator_name} wants to controll you.**",
        colour=0xA343CB
    )
    embed.add_field(
        name="Once someone controlls you they take control over all your special statuses.",
        value="You will no longer be able to change any yourself.",
        inline=False
    )
    embed.add_field(
        name="You cannot revoke these priveliges yourself.",
        value="They can only be revoked if they either remove it themselves, go derelict (are inactive for 7 days), or get removed by an admin.",
        inline=False
    )
    embed.add_field(
        name="If you trust them, they will also take control over setting your kinks and limits.",
        value="You can still set your limits message, but everything else will be taken over.\nYou can always trust them later with `/control trust`",
        inline=False
    )
    embed.add_field(
        name="They will not be notified if you decline.",
        value="Neither will they be notified if you block them with `/block add`",
        inline=False
    )
    embed.add_field(
        name="You can also disable all control requests",
        value="Do this with `/control allow_requests false`",
        inline=False
    )
    embed.set_thumbnail(url=instantiator_picture)

    return embed
