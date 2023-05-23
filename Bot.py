import asyncio
from collections import defaultdict
import os.path
import random

import interactions
import openai
from typing import Dict, List, Set, Tuple

# Set up OpenAI
MODEL = 'gpt-3-5-turbo-discord'
openai.api_key = os.getenv('OPENAI_API_KEY')

bot = interactions.Client(token=os.getenv('BOT_TOKEN'))

question_bank = open(os.path.dirname(__file__) + '/questions.txt')
questions = question_bank.readlines()
vwqf = open(os.path.dirname(__file__) + '/vote_who.txt')
vote_who_questions = vwqf.readlines()

# Vote Who
vote_who_members: Set[interactions.Member] = set()
vote_who_scores: Dict[str, int] = defaultdict(lambda: 0)
vote_who_mappings: Dict[interactions.Snowflake, str] = {}
vote_who_answers: Dict[Tuple[interactions.Snowflake, str], int] = defaultdict(lambda: 0)

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


@bot.command(
    name='openai_test', description='Calls OpenAi to generate questions',
)
async def openai_test(ctx: interactions.CommandContext):
    await ctx.defer()
    prompt = {
        'role': 'user',
        'content': 'Generate 10 question for friends in a Discord server who already know each other well. The questions are funny and quirky. The questions should be answerable in 1-3 open-ended words. They are outputted in numbered list.',
    }
    openai_response = openai.ChatCompletion.create(model=MODEL, temperature=1.0, messages=[prompt])
    openai_result = openai_response.choices[0].message.content
    await ctx.send(openai_result)


@bot.command(
    name='votewhoadd', description='Add user to Vote Who game',
    options=[
        interactions.Option(
            name='member',
            description='users to add to the game',
            type=interactions.OptionType.MENTIONABLE,
            required=True,
        ),
    ],
)
async def votewhoadd(ctx: interactions.CommandContext, member: interactions.Member):
    vote_who_members.add(member)
    await ctx.send(f"Added <@{member.user.id}> to the game")
    # n = len(members)
    # questions = random.sample(vote_who_questions, n)
    # print(members)
    # for question in questions:
    #     await ctx.component(
    #         view=interactions.SelectMenu(placeholder=question, options=[interactions.SelectOption(label=member.display_name, value=member.display_name) for member in members])
    #     )

@bot.component("vote_who")
async def vote_who_response(ctx, response):
    user = response[0]
    vote_who_scores[user] += 1
    vote_who_answers[(ctx.message.id, user)] += 1
    await ctx.message.delete()

@bot.command(
    name='votewhostartround', description='Start a round of the Vote Who game',
)
async def votewhostartround(ctx: interactions.CommandContext):
    n = len(vote_who_members)
    if n > 10:
        await ctx.send("Cannot play with more than 10 people")
    else:
        questions = random.sample(vote_who_questions, n)
        await ctx.send("You have 30 seconds to vote for each question!")
        for question in questions:
            message = await ctx.send(
                components=interactions.SelectMenu(custom_id="vote_who", placeholder=question, options=[interactions.SelectOption(label=member.user.username, value=member.user.username) for member in vote_who_members])
            )
            vote_who_mappings[message.id] = question
        await asyncio.sleep(20)
        await ctx.send("You have 10 seconds left to vote for each question!")
        await asyncio.sleep(10)

        vote_who_dict: Dict[interactions.Snowflake, List[str]] = defaultdict(lambda: [])
        for (q, u), c in vote_who_answers.items():
            vote_who_dict[q].append(f"{u} - {c}")
        vote_who_list: List[Tuple[interactions.Snowflake, str]] = [(q, ','.join(scores)) for q, scores in vote_who_dict.items()]

        vote_who_answers_formatted = '\n'.join([f"{vote_who_mappings[q]}: {a}" for q, a in vote_who_list])
        vote_who_scores_formatted = '\n'.join([f"{u}: {s}" for u, s in vote_who_scores.items()])
        await ctx.send(f"Here were the answers to each question \n {vote_who_answers_formatted}")
        await ctx.send(f"Here are the scores for each player so far \n {vote_who_scores_formatted}")

        vote_who_mappings.clear()
        vote_who_answers.clear()


@bot.command(
    name='votewhoendgame', description='End the Vote Who game and report the scores',
)
async def votewhoendgame(ctx: interactions.CommandContext):
    vote_who_scores_formatted = '\n'.join([f"{u}: {s}" for u, s in vote_who_scores.items()])
    await ctx.send(f"Game over! Here were the scores for each player \n {vote_who_scores_formatted}")

    vote_who_members.clear()
    vote_who_scores.clear()
    vote_who_mappings.clear()
    vote_who_answers.clear()

bot.start()
