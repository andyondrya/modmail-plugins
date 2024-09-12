import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


class EmbedRaw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    async def raw(self, ctx, message_id: int=None):
        if message_id is None:
            return await ctx.send("Please provide a message ID")
        
        try:
            msg = await ctx.fetch_message(message_id)
        except commands.CommandInvokeError:
            return await ctx.send("Message not found")

        await ctx.send(f"```{msg.embeds[0].description}```")
        

async def setup(bot):
    await bot.add_cog(EmbedRaw(bot))
