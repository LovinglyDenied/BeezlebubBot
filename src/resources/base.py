import discord
import discord.ui as ui

from models import ManagedCommandError


class BaseView(ui.View):
    """The Base view all other views should inherit from.
    Features: 
        - Error handeling (disables itself and sends an error embed if not a ManagedCommandError)"""

    async def on_error(self, error: Exception, item: ui.Item, interaction: discord.Interaction):
        self.disable_all_items()
        if isinstance(item, ui.Button):
            item.style = discord.ButtonStyle.red

        if not isinstance(error, ManagedCommandError):
            message = f"An error appeared while processing the command.```{error}```"
            embed: discord.Embed = create_error_embed(message)
            await interaction.message.reply(embed=embed, delete_after=60)

        await interaction.response.edit_message(view=self)
        self.stop()


def create_error_embed(message: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"**Something went wrong!**",
        description=message,
        colour=0xED4245
    )
    return embed


def create_notification_embed(message: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"**You got a notification.**",
        description=message,
        colour=0xA343CB
    )
    return embed
