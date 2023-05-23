import os
import os.path
import random

import interactions
import openai
import asyncio
from interactions import autodefer


# Set up OpenAI
MODEL = 'gpt-3-5-turbo-discord'
openai.api_key = os.getenv('OPENAI_API_KEY')

bot = interactions.Client(token='MTExMDMwOTQ1NTQ5NDY1NjAwMQ.GwpVfV.AnZN9ANJiO5CJrYzDJjYlLig5LK5AA_5azD_zw')

question_bank = open(os.path.dirname(__file__) + '/questions.txt')
questions = question_bank.readlines()

prompt = {
    'role': 'user',
    'content': 'Generate 1 question for friends in a Discord server who already know each other well. The questions are funny and quirky. The questions should be answerable in 1-3 open-ended words. They are outputted in numbered list.',
}
openai_response = openai.ChatCompletion.create(model=MODEL, temperature=0, messages=[prompt])
openai_result = openai_response.choices[0].message.content

@bot.command(
    name='hello_command', description='Just prints "hello"!', scope=1110296888953032837,
)
async def hello(ctx: interactions.CommandContext):
    await ctx.send('Hello World')


@bot.command(
    name='questionbank',
    description='Prints up to 10 questions from the bank',
    scope=1110296888953032837,
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


@bot.command(
    name='openai_test', description='Calls OpenAi to generate questions', scope=1110296888953032837,
)
@autodefer()
async def openai_test(ctx: interactions.CommandContext):
    await ctx.send(openai_result)

bot.start()
