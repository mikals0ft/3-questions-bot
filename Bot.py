import asyncio
import os.path
import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

import interactions
import openai
from interactions import ActionRow, Button, SelectMenu, SelectOption

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
guess_who_answered_answers = []


@bot.command(
    name='guess_who_answered',
    description='Everyone answers a question, then you guess who put each answer!',
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

    guess_who_answered_participants = len(set(guess_who_answered_friends + [ctx.author.mention]))

    global guess_who_answered_answers
    guess_who_answered_answers = []
    global guess_who_answered_votes
    guess_who_answered_votes = [0, 0, 0]
    global users_who_voted_already
    users_who_voted_already = []

    global guess_who_answered_questions
    guess_who_answered_questions = random.sample(question_bank, 3)
    line1 = 'Hey {}! {} has invited you to play Guess Who Answered!\n\n'.format(friends_str, ctx.author.mention)
    line2 = 'How well do YOU know your friends? :thinking:\n\n'
    line3 = 'Vote on a question to answer:\n'
    line4 = ' :one: {} \n :two: {} \n :three: {}\n'.format(
        guess_who_answered_questions[0], guess_who_answered_questions[1], guess_who_answered_questions[2]
    )
    line5 = 'You have up to {} seconds to vote...\n'.format(30)

    s1 = SelectMenu(
        custom_id='voting_menu',
        placeholder='Select a question to vote for',
        options=[
            SelectOption(label='1', value='1'),
            SelectOption(label='2', value='2'),
            SelectOption(label='3', value='3'),
        ],
    )
    await ctx.send(line1 + line2 + line3 + line4 + line5, components=ActionRow.new(s1))

    # Wait until all participants have voted or it's been 30 seconds.
    i = 0
    while len(users_who_voted_already) < guess_who_answered_participants and i < 6:
        await asyncio.sleep(5)
        i += 1
    if i == 6:
        prefix = 'Time is up! \n\n'
    else:
        prefix = 'Everyone voted! \n\n'

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

    i = 0
    while len(guess_who_answered_answers) < guess_who_answered_participants and i < 12:
        await asyncio.sleep(5)
        i += 1
    if i == 12:
        line1 = 'Time is up! \n'
    else:
        line1 = 'Everyone answered! \n'
    line2 = 'Now, can you guess who gave each answer? :mag: \n\n'

    users = [t[0] for t in guess_who_answered_answers]
    answers = [t[1] for t in guess_who_answered_answers]
    random.shuffle(users)
    random.shuffle(answers)

    line3 = 'The answers:\n - ' + '\n- '.join(answers)
    line4 = '\n\nPeople who answered:\n- ' + '\n- '.join(users)
    await ctx.send(line1 + line2 + line3 + line4)

    menus = []
    for answer in answers:
        options = []
        the_user = ''
        for user in users:
            if answer == guess_who_answered_answers[users.index(user)][1]:
                options.append(SelectOption(label=user, value='correct'))
                the_user = user
            else:
                options.append(SelectOption(label=user, value='incorrect'))

        s1 = SelectMenu(custom_id='guessing_menu', placeholder='Who wrote: "' + answer + '"?', options=options,)
        await ctx.send(answer, components=ActionRow.new(s1))


@bot.component('guessing_menu')
async def guessing_menu_response(ctx, response):
    if response[0] == 'correct':
        await ctx.send(ctx.author.mention + ' answered correctly! :white_check_mark:')
    else:
        await ctx.send(ctx.author.mention + ' answered incorrectly! :red_square:')


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
    guess_who_answered_votes[int(response[0]) - 1] += 1

    line1 = 'You voted for Question {} \n'.format(response[0])
    await ctx.send(line1, ephemeral=True)


@bot.modal('answer_modal')
async def modal_response(ctx, response: str):
    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]
    line1 = '**The chosen question was:** {}\n'.format(chosen_question)
    line2 = 'And you answered: {}\n'.format(response)
    line3 = 'Waiting for others to answer...\n'
    global guess_who_answered_answers
    guess_who_answered_answers.append((ctx.author.name, response))
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
        await ctx.send('You have 30 seconds to vote for each question!')
        for question in questions:
            message = await ctx.send(
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
        await asyncio.sleep(20)
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


bot.start()
