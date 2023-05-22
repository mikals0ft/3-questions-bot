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


class EscapeRoom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def unlockroom(self, ctx, room_name):
        """
        Picks a random user from the server to win your giveaway.
        """
        if room_name in VALID_ROOM_ROLES:
            room_role: Role = discord.utils.get(ctx.guild.roles, name=room_name)
            attendees_role: Role = discord.utils.get(ctx.guild.roles, name=ATTENDEE_ROLE_NAME)
            for user in attendees_role.members:
                await user.add_roles(room_role, atomic=True)
            await ctx.send(f'{room_name} unlocked')
        else:
            await ctx.send(f'Must specify a valid room role out of the following: {",".join(VALID_ROOM_ROLES)}')

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        roles = [role.name for role in after.roles]
        if 'room-3a-complete' in roles and 'room-3b-complete' in roles and 'room-3c-complete' in roles:
            room_4_role: Role = discord.utils.get(after.guild.roles, name='room-4')
            await after.add_roles(room_4_role, atomic=True)
            # await after.send('Room 4 unlocked')
        if 'room-5a-complete' in roles and 'room-5b-complete' in roles:
            room_6_role: Role = discord.utils.get(after.guild.roles, name='room-6')
            await after.add_roles(room_6_role, atomic=True)
            # await after.send('Room 6 unlocked')

    @commands.Cog.listener()
    async def on_member_join(self, after: Member):
        newbie_role = discord.utils.get(after.guild.roles, name='Escape Room Attendee')
        landing_zone_channel = discord.utils.get(after.guild.channels, name="landing-zone")
        await after.add_roles(newbie_role)
        if landing_zone_channel is not None:
            await landing_zone_channel.send(LZ_WELCOME.format(after))

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        user_id = message.author.id
        if user_id == CARL_BOT_ID:
            channel = message.channel
            guild = message.guild
            if channel.name == 'room-1':
                if message.content == "Room 1 complete":
                    await self.unlock_role(guild, channel, 'room-2')
            elif channel.name == 'room-2':
                if message.content == "Room 2 complete":
                    await self.unlock_role(guild, channel, 'room-3')
            elif channel.name == 'room-3a':
                if message.content == "Room 3a complete":
                    await self.unlock_role(guild, channel, 'room-3a-complete')
            elif channel.name == 'room-3b':
                if message.content == "Room 3b complete":
                    await self.unlock_role(guild, channel, 'room-3b-complete')
            elif channel.name == 'room-3c':
                if message.content == "Room 3c complete":
                    await self.unlock_role(guild, channel, 'room-3c-complete')
            elif channel.name == 'room-4':
                if message.content == "Room 4 complete":
                    await self.unlock_role(guild, channel, 'room-5')
            elif channel.name == 'room-5a':
                if message.content == "Room 5a complete":
                    await self.unlock_role(guild, channel, 'room-5a-complete')
            elif channel.name == 'room-5b':
                if message.content == "Room 5b complete":
                    await self.unlock_role(guild, channel, 'room-5b-complete')
            elif channel.name == 'room-6':
                if message.content == "Room 6 complete":
                    await self.unlock_role(guild, channel, 'final-room')
            elif channel.name == 'final-room':
                if "End time is " in message.content:
                    await self.unlock_role(guild, channel, 'escape-room-complete')

    async def unlock_role(self, guild, channel, room_name):
        if room_name in VALID_ROOM_ROLES:
            room_role: Role = discord.utils.get(guild.roles, name=room_name)
            attendees_role: Role = discord.utils.get(guild.roles, name=ATTENDEE_ROLE_NAME)
            for user in attendees_role.members:
                await user.add_roles(room_role, atomic=True)
            if room_name == 'room-3':
                await channel.send('room-3a, room-3b, and room-3c unlocked. You must complete all 3 to unlock the next room.')
            elif room_name == 'room-5':
                await channel.send('room-5a and room-5b unlocked. You must complete both of them to unlock the next room.')
            elif room_name not in ['room-3a-complete', 'room-3b-complete', 'room-3c-complete', 'room-5a-complete', 'room-5b-complete']:
                await channel.send(f'{room_name} unlocked')
        else:
            await channel.send(f'Must specify a valid room role out of the following: {",".join(VALID_ROOM_ROLES)}')

    @commands.command()
    async def wungusfoodtour(self, ctx):
        conditions = [False] * 4
        message = await ctx.send(FOOD_TOUR_INTRO_MESSAGE)
        while not all(condition for condition in conditions):
            conditions = await wait_for_reactions_on_message(message, self.bot, conditions)
            words_guessed = ",".join(map(operator.itemgetter(0), filter(lambda x: x[1], zip(FOOD_TOUR_SOLUTIONS, conditions))))
            await ctx.send(f'{sum(conditions)} out of 4 items delivered. Words guessed correctly so far: {words_guessed}')

        await ctx.send('Room 5a complete')
        # TODO: Give escape room participators role to unlock next room(s)
        await self.unlock_role(ctx.guild, ctx.channel, 'room-5a-complete')


def setup(bot):
    bot.add_cog(EscapeRoom(bot))
