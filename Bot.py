import asyncio
import os.path
import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import interactions
import openai
from interactions import ActionRow, Button, SelectMenu, SelectOption
from crontab import CronTab

# Set up OpenAI
MODEL = 'gpt-3-5-turbo-discord'
openai.api_key = os.getenv('OPENAI_API_KEY')

bot = interactions.Client(token=os.getenv('BOT_TOKEN'))

question_bank_file = open(os.path.dirname(__file__) + '/questions.txt')
question_bank = question_bank_file.readlines()


@bot.command(
    name='hello_command', description='Just prints "hello"!',
)
async def hello(ctx: interactions.CommandContext):
    await ctx.send('Hello World')


@bot.command(
    name='test_new_command', description='Just prints "hello"!',
)
async def test_new_command(ctx: interactions.CommandContext):
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
        top_n_questions = '\n'.join(random.sample(question_bank, num_questions))
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


########################## GuessWhoAnswered ###########################
#### GLOBAL VARIABLES ####
guess_who_answered_votes = []
users_who_voted_already = []
guess_who_answered_participants = 0
guess_who_answered_questions = []
guess_who_answered_answers = {}


@bot.command(
    name='guesswho',
    description='Vote on a question to get to know your friends better, then guess who answered what!',
    options=[
        interactions.Option(
            name='friend1',
            description='Optionally invite some friends to join',
            type=interactions.OptionType.STRING,
            required=False,
        ),
        interactions.Option(
            name='friend2',
            description='Optionally invite some friends to join',
            type=interactions.OptionType.STRING,
            required=False,
        ),
        interactions.Option(
            name='friend3',
            description='Optionally invite some friends to join',
            type=interactions.OptionType.STRING,
            required=False,
        ),
    ],
)
async def guess_who_answered(ctx: interactions.CommandContext, friend1: str = '', friend2: str = '', friend3: str = ''):
    global guess_who_answered_participants
    guess_who_answered_friends = []
    if friend1:
        guess_who_answered_friends.append(str(friend1))
    if friend2:
        guess_who_answered_friends.append(str(friend2))
    if friend3:
        guess_who_answered_friends.append(str(friend3))
    friends_str = ', '.join(guess_who_answered_friends)

    current_user = ctx.author.mention
    guess_who_answered_participants = len(set(guess_who_answered_friends))

    global guess_who_answered_answers
    guess_who_answered_answers = {}
    global guess_who_answered_votes
    guess_who_answered_votes = [0, 0, 0]
    global users_who_voted_already
    users_who_voted_already = []

    global guess_who_answered_questions
    guess_who_answered_questions = random.sample(question_bank, 3)
    max_seconds_per_step = 30
    game_instructions = f"Hey {friends_str}! {current_user} has invited you to play Guess Who Answered!\n\nHow well do YOU know your friends? :thinking:\n\nYou have up to {max_seconds_per_step} seconds to vote...\n\nVote on a question to answer:"

    s1 = SelectMenu(
        custom_id='voting_menu',
        placeholder='Select a question to vote for',
        options=[
            SelectOption(label=question, value=i) for i, question in enumerate(guess_who_answered_questions)
        ],
    )
    await ctx.send(game_instructions, components=ActionRow.new(s1))

    # Wait until (all participants voted or there's only one participant) or until it's been 30 seconds.
    i = 0
    while i < max_seconds_per_step:
        if guess_who_answered_participants == len(users_who_voted_already):
            break
        await asyncio.sleep(1)
        i += 1
    if i == max_seconds_per_step:
        prefix = 'Time is up! \n\n'
    else:
        prefix = 'Votes are in! \n\n'

    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]

    b1 = Button(style=1, custom_id='b1', label='press me')
    await ctx.send(
        prefix
        + '**The chosen question was:** '
        + chosen_question
        + '\nYou have up to 60 seconds to answer! \n\nPress this button to answer:',
        components=ActionRow.new(b1),
    )

    # Wait while (all participants have not voted and it has not been 30 seconds.
    i = 0
    while i < max_seconds_per_step:
        if guess_who_answered_participants == len(guess_who_answered_answers):
            break
        await asyncio.sleep(5)
        i += 1
    if i == max_seconds_per_step:
        line1 = 'Time is up! \n'
    else:
        line1 = 'Everyone answered! \n'
    line2 = 'Now, can you guess who gave each answer? :mag: \n\n'

    users = list(guess_who_answered_answers.keys())
    answers = list(guess_who_answered_answers.values())
    random.shuffle(users)
    random.shuffle(answers)

    for answer in answers:
        options = []
        for user in users:
            if answer == guess_who_answered_answers[user]:
                options.append(SelectOption(label=user, value='correct'))
            else:
                options.append(SelectOption(label=user, value='incorrect'))

        s1 = SelectMenu(custom_id=f'guessing_menu', placeholder='Who answered: "' + answer + '"?', options=options)
        await ctx.send(f"Select who answered: {answer}", components=ActionRow.new(s1))

# Map user to their score
guess_who_answered_scores = {}

@bot.component('guessing_menu')
async def guessing_menu_response(ctx, response):
    global guess_who_answered_scores
    if ctx.author.mention not in guess_who_answered_scores:
        guess_who_answered_scores[ctx.author.mention] = [0,0]
    if response[0] == 'correct':
        guess_who_answered_scores[ctx.author.mention][0] += 1
    else:
        guess_who_answered_scores[ctx.author.mention][1] += 1
    if guess_who_answered_scores[ctx.author.mention][0] + guess_who_answered_scores[ctx.author.mention][1] == len(guess_who_answered_answers):
        message = "{} got {}/{} correct!".format(ctx.author.mention, guess_who_answered_scores[ctx.author.mention][0], len(guess_who_answered_answers))
        await ctx.send(message)
    else:
        await ctx.send("Guess recorded!", ephemeral=True)

@bot.component('b1')
async def b1_response(ctx):
    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]
    modal = interactions.Modal(
        title="It's time to give your answer",
        custom_id='answer_modal',
        components=[
            interactions.TextInput(
                style=interactions.TextStyleType.PARAGRAPH,
                label='The chosen question was:',
                placeholder=chosen_question,
                custom_id='text_input_response',
                min_length=1,
                max_length=100,
            ),
        ],
    )
    await ctx.popup(modal)


@bot.component('voting_menu')
async def voting_menu_response(ctx, response):
    if ctx.author.id in users_who_voted_already:
        await ctx.send('Uhh, you already voted :no_mouth:')
        return
    
    users_who_voted_already.append(ctx.author.id)
    chosen_idx = int(response[0])
    guess_who_answered_votes[chosen_idx] += 1

    line1 = 'You voted for: {} \n'.format(guess_who_answered_questions[chosen_idx])
    await ctx.send(line1, ephemeral=True)


@bot.modal('answer_modal')
async def modal_response(ctx, response: str):
    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]
    line1 = '**The chosen question was:** {}\n'.format(chosen_question)
    line2 = 'And you answered: {}\n'.format(response)
    line3 = 'Waiting for others to answer...\n'
    global guess_who_answered_answers
    guess_who_answered_answers[ctx.author.name] = response
    await ctx.send(line1 + line2 + line3, ephemeral=True)


########################## VoteWho ###########################
#### GLOBAL VARIABLES ####
vwqf = open(os.path.dirname(__file__) + '/vote_who.txt')
vote_who_questions = vwqf.readlines()
vote_who_members: Set[interactions.Member] = set()
vote_who_scores: Dict[str, int] = defaultdict(lambda: 0)
vote_who_mappings: Dict[interactions.Snowflake, str] = {}
vote_who_answers: Dict[Tuple[interactions.Snowflake, str], int] = defaultdict(lambda: 0)


@bot.command(
    name='votewhoadd',
    description='Add user to Vote Who game',
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
    await ctx.send(f'Added <@{member.user.id}> to the game')


@bot.component('vote_who')
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
        await ctx.send('Cannot play with more than 10 people')
    else:
        questions = random.sample(vote_who_questions, n)
        await ctx.send('You have 20 seconds to vote for each question!')
        for question in questions:
            message = await ctx.send(
                question,
                components=interactions.SelectMenu(
                    custom_id='vote_who',
                    placeholder=question,
                    options=[
                        interactions.SelectOption(label=member.user.username, value=member.user.username)
                        for member in vote_who_members
                    ],
                )
            )
            vote_who_mappings[message.id] = question
        await asyncio.sleep(10)
        await ctx.send('You have 10 seconds left to vote for each question!')
        await asyncio.sleep(10)

        vote_who_dict: Dict[interactions.Snowflake, List[str]] = defaultdict(lambda: [])
        for (q, u), c in vote_who_answers.items():
            vote_who_dict[q].append(f'{u} - {c}')
        vote_who_list: List[Tuple[interactions.Snowflake, str]] = [
            (q, ','.join(scores)) for q, scores in vote_who_dict.items()
        ]

        vote_who_answers_formatted = '\n'.join([f'{vote_who_mappings[q]}: {a}' for q, a in vote_who_list])
        vote_who_scores_formatted = '\n'.join([f'{u}: {s}' for u, s in vote_who_scores.items()])
        await ctx.send(f'Here were the answers to each question \n {vote_who_answers_formatted}')
        await ctx.send(f'Here are the scores for each player so far \n {vote_who_scores_formatted}')

        vote_who_mappings.clear()
        vote_who_answers.clear()


@bot.command(
    name='votewhoendgame', description='End the Vote Who game and report the scores',
)
async def votewhoendgame(ctx: interactions.CommandContext):
    vote_who_scores_formatted = '\n'.join([f'{u}: {s}' for u, s in vote_who_scores.items()])
    await ctx.send(f'Game over! Here were the scores for each player \n {vote_who_scores_formatted}')

    vote_who_members.clear()
    vote_who_scores.clear()
    vote_who_mappings.clear()
    vote_who_answers.clear()


########################## QOTD ###########################
#### GLOBAL VARIABLES ####


import asyncio
from contextlib import suppress


class Periodic:
    def __init__(self, func):
        self.func = func
        self.is_started = False
        self._task = None

    async def start(self, ctx, time):
        if not self.is_started:
            self.is_started = True
            # Start task to call func periodically:
            self._task = asyncio.ensure_future(self._run(ctx, time))

    async def stop(self):
        if self.is_started:
            self.is_started = False
            # Stop task and await it stopped:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self, ctx, time):
        while True:
            await self.func(ctx)
            await asyncio.sleep(time * 60)


async def schedule_question(ctx: interactions.CommandContext):
    question = random.sample(question_bank, 1)[0]
    message = await ctx.send(question)
    await message.create_thread(question)

schedule = Periodic(func=schedule_question)


@bot.command(
    name='qotd_start', description='Enable the bot to ask a question and create a thread for server members to discuss',
    options=[
        interactions.Option(
            name='mins',
            description='frequency in which the bot creates the question thread',
            type=interactions.OptionType.INTEGER,
            required=True,
        ),
    ],
)
async def qotd_start(ctx: interactions.CommandContext, mins: int):
    await ctx.send(f"I will create a question thread in this channel every {mins} minutes")
    await schedule.start(ctx, mins)

@bot.command(
    name='qotd_end', description='Stop bot from sending questions'
)
async def qotd_start(ctx: interactions.CommandContext):
    await ctx.send(f"I will no longer create question threads in this channel")
    await schedule.stop()


bot.start()
