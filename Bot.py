import os
import os.path
import random

import interactions
import openai
from interactions import autodefer

# Set up OpenAI
MODEL = 'gpt-3-5-turbo-discord'
openai.api_key = os.getenv('OPENAI_API_KEY')

bot = interactions.Client(token=os.getenv('BOT_TOKEN'))

question_bank = open(os.path.dirname(__file__) + '/questions.txt')
questions = question_bank.readlines()

@bot.command(
    name='hello_command', description='Just prints "hello"!',
)
async def hello(ctx: interactions.CommandContext):
    await ctx.send('Hello World')


@bot.command(
    name='questionbank',
    description='Prints up to 10 questions from the bank',
    options=[
        interactions.Option(
            name='num_questions',
            description='number of questions to output',
            type=interactions.OptionType.INTEGER,
            required=True,
        ),
    ],
)
async def questionbank(ctx: interactions.CommandContext, num_questions: int):
    if num_questions > 10:
        await ctx.send('Cannot output more than 10 questions from question bank')
    else:
        top_n_questions = '\n'.join(random.sample(questions, num_questions))
        await ctx.send(top_n_questions)

async def voteWho(self, ctx: interactions.CommandContext, *members: interactions.Member):
    n = len(members)
    if n > 10:
        await ctx.send("Cannot play with more than 10 people")
    else:
        questions = random.sample(self.vote_who_questions, n)
        print(members)
        for question in questions:
            await ctx.component(
                view=interactions.SelectMenu(placeholder=question, options=[interactions.SelectOption(label=member.display_name, value=member.display_name) for member in members])
            )


@bot.command(
    name='openai_test', description='Calls OpenAi to generate questions',
)
@autodefer()
async def openai_test(ctx: interactions.CommandContext):
    await ctx.defer()
    prompt = {
        'role': 'user',
        'content': 'Generate 10 question for friends in a Discord server who already know each other well. The questions are funny and quirky. The questions should be answerable in 1-3 open-ended words. They are outputted in numbered list.',
    }
    openai_response = openai.ChatCompletion.create(model=MODEL, temperature=0, messages=[prompt])
    openai_result = openai_response.choices[0].message.content
    await ctx.send(openai_result)

bot.start()
