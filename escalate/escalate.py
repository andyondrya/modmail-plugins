import traceback
import discord 

from discord.ext import commands 

from core import checks 
from core.models import PermissionLevel

class EscalateThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.plugin_db.get_partition(self)
        self.config = None
        self.default_config = {'terminology': 'thread', 'options': {}}
    
    async def cog_load(self):
        self.config = await self.db.find_one({ "_id": "escalatethread"})
        if self.config is None:
            self.config = self.default_config
            await self.update_config()

        missing = []
        for key in self.default_config.keys():
            if key not in self.config:
                missing.append(key)

        if missing:
            for key in missing:
                self.config[key] = self.default_config[key]

        await self.update_config()

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "escalatethread"},
            {"$set": self.config},
            upsert=True,
        )
    
    @checks.has_permissions(PermissionLevel.SUPPORTER)
    @checks.thread_only()
    @commands.command()
    async def escalate(self, ctx, dept):
        """Escalate your thread/ticket to a specific department"""
        category = discord.utils.get(ctx.guild.categories, id=self.config['options'][dept]['category'])
        if dept not in self.config['options']:
            options = f"\n".join(key for key in self.config['options'].keys())
            embed = discord.Embed(title="Escalation Options", color=discord.Color.red(),
                                    description=f"That department doesn't exist. Your available options are:\n\n{options}")
            return await ctx.send(embed=embed)
        
        await ctx.channel.move(
            category=category, reason=f"{ctx.author} escalated this {self.config['terminology']}.", end=True
        )
        await ctx.send(f"<@&{self.config['options'][dept]['role']}>")
        
        ctx.message.content = f"Your {self.config['terminology']} is being escalated to {dept.title()}."
        await ctx.thread.reply(ctx.message, anonymous=True)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.group(invoke_without_command=True)
    async def escalatethread(self, ctx):
        """Setup categories to escalate your threads/tickets to"""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @escalatethread.group(name='config', invoke_without_command=True)
    async def escalationthread_config(self, ctx):
        """Take a peek at your current escalation config""" 
        embed = discord.Embed(title='Escalate Thread Configuration', color=discord.Color.blurple())
        embed.add_field(name="Terminology", value=self.config['terminology'])
        await ctx.send(embed=embed)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @escalatethread.group(name='set', invoke_without_command=True)
    async def escalationthread_set(self, ctx):
        """Set a new value for an option"""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @escalationthread_set.command(name='terminology', invoke_without_command=True)
    async def escalationthread_config_set(self, ctx, option: str):
        """Set your terminology""" 
        allowed_values = ['thread', 'ticket']
        if option not in allowed_values:
            return await ctx.send("You must pick `thread` or `ticket`")
        
        self.config['terminology'] = option
        await self.update_config()
        await ctx.send(f"Successfully updated the terminology to {option}")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @escalatethread.command(name='add', invoke_without_command=True)
    async def escalationthread_add(self, ctx, name: str, role: discord.Role, category: discord.CategoryChannel):
        """Add an option to escalate to."""
        name = name.lower()

        if name in self.config['options']:
            return await ctx.send("This option already exists. Modify or delete it to continue.")

        self.config['options'][name] = {
            'role': role.id,
            'category': category.id
        }
        
        await self.update_config()
        await ctx.send(f"Added! Escalating to `{name}` will mention <@&{role.id}> and moved to `{category.name}`")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @escalatethread.command(aliases=['remove', 'del'],name='delete', invoke_without_command=True)
    async def escalationthread_delete(self, ctx, name: str):
        """Pick an option to delete."""
        name = name.lower()

        if name not in self.config['options']:
            return await ctx.send("This option doesn't exist. Was it already deleted?")

        del self.config['options'][name]

        await self.update_config()
        await ctx.send(f"Successfully removed `{name}`")

async def setup(bot):
    await bot.add_cog(EscalateThread(bot))
