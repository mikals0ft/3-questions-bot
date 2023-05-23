from discord.ext import commands
from discord.member import Member
from discord.message import Message
from discord.role import Role
import discord.utils
import os
import os.path
import openai
import random
import discord
from discord.ext import commands


openai.api_key = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-3-5-turbo-discord'


class Select(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Select an option",max_values=len(options), min_values=1,options=options)

class SelectView(discord.ui.View):
    def __init__(self, *, options, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(Select(options=options))

class ThreeQuestions(commands.Cog):
    def __init__(self, bot):
        qf = open(os.path.dirname(__file__) + '/../../questions.txt')
        vwqf = open(os.path.dirname(__file__) + '/../../vote_who.txt')
        self.bot = bot
        self.questions = qf.readlines()
        self.vote_who_questions = vwqf.readlines()

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

    @commands.command()
    async def voteWho(self, ctx, *members: discord.Member):
        n = len(members)
        if n > 10:
            await ctx.send("Cannot play with more than 10 people")
        else:
            questions = random.sample(self.vote_who_questions, n)
            print(members)
            for question in questions:
                embed = discord.Embed(title = question)
                await ctx.send(
                    embed=embed,
                    view=SelectView(options=[discord.SelectOption(label=member.display_name, value=member.display_name) for member in members])
                )
            for question in questions:
                await ctx.send(question)
    
    @commands.command()
    async def question(self, ctx):
        prompt = {
            'role': 'user',
            'content': 'Generate 10 questions for friends in a Discord server who already know each other well. The questions are funny and quirky. The questions should be answerable in 1-3 open-ended words. They are outputted in numbered list.',
        }
        response = openai.ChatCompletion.create(model=MODEL, temperature=0, messages=[prompt])

        result = response.choices[0].message.content
        print(result)
        await ctx.send(result)


def setup(bot):
    bot.add_cog(ThreeQuestions(bot))
