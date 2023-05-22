from helpers import wait_for_reactions_on_message
from constants import FOOD_TOUR_INTRO_MESSAGE, FOOD_TOUR_SOLUTIONS
import operator

from constants import ATTENDEE_ROLE_NAME, CARL_BOT_ID, VALID_ROOM_ROLES
from constants import LZ_WELCOME
from discord.ext import commands
from discord.member import Member
from discord.message import Message
from discord.role import Role
import discord.utils


class ThreeQuestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        print(message.content)

    @commands.command()
    async def hello(self, ctx):
        print('hai')
        await ctx.send(f'Hello World')


def setup(bot):
    bot.add_cog(ThreeQuestions(bot))
