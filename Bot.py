import discord
from Functions.ThreeQuestions.threequestions import ThreeQuestions
from discord.ext import commands
import os

import settings

intents = discord.Intents.all()

intents.members = True

cogs: list = ["Functions.ThreeQuestions.threequestions"]


bot = commands.Bot(command_prefix=settings.Prefix, help_command=None, intents=intents)


@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(settings.BotStatus))
    await bot.add_cog(ThreeQuestions(bot))

bot.run(os.environ['BOT_TOKEN'])
