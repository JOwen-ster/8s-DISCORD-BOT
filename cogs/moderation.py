import discord
from discord.ext import commands, tasks
from utils.loggingsetup import getlog


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Repeating background task using the asyncio discord.ext tasks decorator
    @tasks.loop(minutes=5.0)
    async def update_status(self):
        await self.bot.change_presence(activity=discord.Game(name=F'Hosting 8s in {len(self.bot.guilds)} Servers!'))
        getlog().info(F'RAN TASK: Update Status')

    @update_status.before_loop
    async def before_update_status(self):
        getlog().info('TASK WAITING UNTIL READY: Update Status')
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Moderation(bot))
