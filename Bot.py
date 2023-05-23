import os
import os.path
import random

import interactions
import openai
from interactions import autodefer
from interactions import ActionRow, Button, SelectMenu, SelectOption
import asyncio

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
        top_n_questions = '\n'.join(random.sample(questions, num_questions))
        await ctx.send(top_n_questions)


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
        )
    ],
)
async def guess_who_answered(ctx: interactions.CommandContext, friend1: str = "", friend2: str = "", friend3: str = ""):
    global guess_who_answered_participants
    guess_who_answered_friends = []
    if friend1:
        guess_who_answered_friends.append(str(friend1))
    if friend2:
        guess_who_answered_friends.append(str(friend2))
    if friend3:
        guess_who_answered_friends.append(str(friend3))
    friends_str = ", ".join(guess_who_answered_friends)
    
    guess_who_answered_participants = len(guess_who_answered_friends) + 1
    
    global guess_who_answered_answers
    guess_who_answered_answers = []
    global guess_who_answered_votes
    guess_who_answered_votes = [0, 0, 0]
    global users_who_voted_already
    users_who_voted_already = []
    
    global guess_who_answered_questions
    guess_who_answered_questions = random.sample(question_bank, 3)
    line1 = "Hey {}! {} has invited you to play Guess Who Answered!\n\n".format(friends_str, ctx.author.mention)
    line2 = "How well do YOU know your friends? :thinking:\n\n"
    line3 = "Vote on a question to answer:\n"
    line4 = " :one: {} \n :two: {} \n :three: {}\n".format(guess_who_answered_questions[0], guess_who_answered_questions[1], guess_who_answered_questions[2])
    line5 = "You have {} seconds to vote...\n".format(30)
    
    
    s1 = SelectMenu(
        custom_id="voting_menu",
        placeholder = "Select a question to vote for",
        options=[
            SelectOption(label="1", value="1"),
            SelectOption(label="2", value="2"),
            SelectOption(label="3", value="3"),
        ],
    )
    await ctx.send(line1+line2+line3+line4+line5, components=ActionRow.new(s1))
    
    await asyncio.sleep(30)
    
    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]

    b1 = Button(style=1, custom_id="b1", label="press me")    
    await ctx.send("The chosen question was: " + chosen_question + "\n Press this button to answer:", components=ActionRow.new(b1))

@bot.component("b1")
async def b1_response(ctx):
    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]
    modal = interactions.Modal(
        title="It's time to give your answer",
        custom_id="answer_modal",
        components=[
            interactions.TextInput(
                style=interactions.TextStyleType.PARAGRAPH,
                label="The chosen question was:",
                placeholder = chosen_question,
                custom_id="text_input_response",
                min_length=1,
                max_length=200
            ),
        ],
    )
    await ctx.popup(modal)

@bot.component("voting_menu")
async def voting_menu_response(ctx, response):
    if (ctx.author.id in users_who_voted_already):
        await ctx.send("Uhh, you already voted :no_mouth:")
        return
    users_who_voted_already.append(ctx.author.id)
    guess_who_answered_votes[int(response[0])-1] += 1

    line1 = "You voted for Question {} \n".format(response[0])
    await ctx.send(line1, ephemeral=True)

@bot.modal("answer_modal")
async def modal_response(ctx, response: str):
    index = guess_who_answered_votes.index(max(guess_who_answered_votes))
    chosen_question = guess_who_answered_questions[index]
    line1 = "The chosen question was: {}\n".format(chosen_question)
    line2 = "And you answered: {}\n".format(response)
    line3 = "Waiting for others to answer...\n"
    global guess_who_answered_answers
    guess_who_answered_answers.append(response)
    if len(guess_who_answered_answers) == guess_who_answered_participants:
        await ctx.send("Everyone answered, the answers were: " +  ", ".join(guess_who_answered_answers))
    else:
        await ctx.send(line1+line2+line3, ephemeral=True)

bot.start()
