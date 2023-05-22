from discord.ext import commands
from discord.member import Member
from discord.message import Message
from discord.role import Role
import discord.utils
import os.path
import random


class ThreeQuestions(commands.Cog):
    def __init__(self, bot):
        qf = open(os.path.dirname(__file__) + '/../../questions.txt')
        self.bot = bot
        self.questions = qf.readlines()

    # @commands.Cog.listener()
    # async def on_message(self, message: Message):
    #     print(message.content)

    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f'Hello World')

    @commands.command()
    async def questionbank(self, ctx, n: int):
        if n > 10:
            await ctx.send("Cannot output more than 10 questions from question bank")
        else:
            questions = random.sample(self.questions, n)
            for question in questions:
                await ctx.send(question)

def setup(bot):
    bot.add_cog(ThreeQuestions(bot))
