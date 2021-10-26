import asyncio
import datetime
import gettext
import os

import pytz
import tortoise
from discord.ext import commands

from catfish_discord.util.alttpr import get_preset
from catfish_discord.util.alttpr_disord import get_embed
from models.models import Race, Participant, GuildSettings

translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext


class AlttprRace(commands.Cog):
    tz = pytz.timezone(os.getenv("TIMEZONE", 'Europe/Berlin'))
    _tasks = dict()

    async def _create_tasks(self):
        await asyncio.sleep(5)
        races = await Race.filter(finished=False).all()
        for race in races:
            print(f"Race {race.id} is again stated.")
            guild = self.bot.get_guild(race.guild)
            guild_settings = await GuildSettings.filter(guild=race.guild).first()
            task = asyncio.create_task(self._start_race(guild.get_channel(guild_settings.race_channel_id), race))
            self._tasks[race.id] = task

    def __init__(self, bot):
        self.bot = bot
        asyncio.get_event_loop().create_task(self._create_tasks())

    @commands.group(pass_context=True, invoke_without_command=True)
    async def race(self, ctx):
        if ctx.invoked.subcommand is None:
            await self.bot.say(_("Invalid command, please use subcommands."))

    async def _start_race(self, channel, race):
        now = datetime.datetime.now(self.tz)
        delta = (race.date - now) - datetime.timedelta(minutes=10)
        if delta.total_seconds() > 0:
            await asyncio.sleep(delta.total_seconds())
            await channel.send(_("Registration is now closed, and race will start in 10 minutes."))
        else:
            await channel.send(_("Bot is crashed and will start the game in 10 minutes."))
        # Close registration
        race.open = False
        await race.save()

        # Generate new seed
        await channel.send(_("Please download this seed for the current race."))
        seed = await get_preset(race.preset, hints=False, spoilers="off", allow_quickswap=True)
        emojis = self.bot.get_guild(859817345743978497).emojis
        embed = await get_embed(emojis, seed)
        await channel.send(embed=embed)
        race.seed = seed.url
        await race.save()
        # Countdown
        await asyncio.sleep(300)
        await channel.send(_("Race will start in around 5 minutes."))
        await asyncio.sleep(240)
        await channel.send(_("Race will start in around 1 minutes."))
        await asyncio.sleep(30)
        await channel.send(_("Race will start in around 30 seconds."))
        await asyncio.sleep(20)
        await channel.send(_("Race will start in around 10 seconds."))
        await asyncio.sleep(7)
        await channel.send(_("Race will start in around 3 seconds."))
        await asyncio.sleep(1)
        await channel.send("2")
        await asyncio.sleep(1)
        await channel.send("1")
        await asyncio.sleep(1)
        await channel.send(_("Race is stated. Good luck."))
        race.ongoing = True
        await race.save()

    @race.command(
        brief=_('Start a new race game.'),
        help=_('Start a new race game.'),
        invoke_without_command=True,
        pass_context=True
    )
    async def start(self, ctx, time, preset):
        # Check if the channel id is valid
        guild_settings = await GuildSettings.filter(guild=ctx.guild.id).first()
        if ctx.message.channel.id != guild_settings.race_registration_channel_id:
            return
        now = datetime.datetime.now(self.tz)
        race_time = datetime.datetime.strptime(time, '%H:%M')
        start_time = now.replace(hour=race_time.hour, minute=race_time.minute, second=0)
        delta = start_time - now
        if delta < datetime.timedelta(minutes=10):
            await ctx.reply(_("Please start a race game more then 10 minutes before."))
            return

        races = await Race.filter(author_id=ctx.author.id, finished=False).all()
        if len(races) > 0:
            await ctx.reply(
                _('Please finish you old race before you start a new one. Race ID: ' + f"{races[0].id}"))
            return
        race = await Race.create(preset=preset, author_id=ctx.author.id, author=ctx.author.name,
                                 date=start_time, guild=ctx.guild.id)

        task = asyncio.create_task(self._start_race(ctx.guild.get_channel(guild_settings.race_channel_id), race))
        self._tasks[race.id] = task
        await ctx.author.send(_('New race is generated. Race ID: ') + f"{race.id}")
        await ctx.reply(_('New race is generated. Race ID: ') + f"{race.id}")

        race_channel = self.bot.get_guild(race.guild).get_channel(guild_settings.race_channel_id)
        await race_channel.send(_('New race is generated. Race ID: ') + f"{race.id}")
        await race_channel.send('================================')
        await race_channel.send(_("Participants:"))

    async def _remove_roles(self, guild, participants, roles, delay):
        await asyncio.sleep(delay)
        for p in participants:
            member = guild.get_member(p.player_id)
            await member.remove_roles(*roles)

    async def _stop_race(self, race):
        task = self._tasks[race.id]
        try:
            task.cancel()
            await task
        except:
            print("Exception ocurred")
        del self._tasks[race.id]

        guild = self.bot.get_guild(race.guild)
        guild_settings = await GuildSettings.filter(guild=race.guild).first()
        roles = list(filter(lambda r: r.id == guild_settings.race_active_role
                                      or r.id == guild_settings.race_finish_role, guild.roles))
        participants = await Participant.filter(race=race).all()

        # Check if the race were already started
        anyone_ends = False
        if race.ongoing:
            for p in participants:
                if not p.end_time:
                    anyone_ends = True
                    break

        # Remove roles
        asyncio.create_task(self._remove_roles(guild, participants, roles, 1800 if anyone_ends else 0))

        race.ongoing = False
        race.finished = True
        await race.save()

        await self._clean_channel(guild.get_channel(guild_settings.race_channel_id))
        await self._clean_channel(guild.get_channel(guild_settings.race_registration_channel_id))
        await self._clean_channel(guild.get_channel(guild_settings.race_chat_channel_id))
        await self._clean_channel(guild.get_channel(guild_settings.race_result_channel_id))

    async def _clean_channel(self, channel):
        messages = await channel.history(limit=200).flatten()
        for message in messages:
            await message.delete()

    @race.command(
        brief=_('Stop a race game.'),
        help=_('Stop a new race game.'),
        invoke_without_command=True,
        pass_context=True
    )
    async def stop(self, ctx, id=None):
        # Check if the channel id is valid
        guild_settings = await GuildSettings.filter(guild=ctx.guild.id).first()
        if ctx.message.channel.id != guild_settings.race_registration_channel_id:
            return

        if not id:
            race = await Race.filter(author_id=ctx.author.id, finished=False).first()
        else:
            race = await Race.filter(id=id).first()

        if race:
            await self._stop_race(race)
            await ctx.reply(_('You stopped the race with id: ') + f"{race.id}")

    async def _result(self, race, channel):
        participants = await Participant.filter(race=race).order_by('time')
        await channel.send(f"======== Race {race.id}  -  {race.preset} ========")
        await channel.send(f"Seed: {race.seed}")
        count = 1
        for player in participants:
            time = "None" if player.time > datetime.timedelta(days=1) or player.resign else f"{player.time}"
            await channel.send(f"#{count} - {player.player} - Time: {time}")
            count = count + 1

    @race.command(
        brief=_('Get the result of an race.'),
        help=_('Get the result of an race.'),
        invoke_without_command=True,
        pass_context=True
    )
    async def result(self, ctx, id):
        race = await Race.filter(id=id).first()
        channel = ctx.message.channel
        await self._result(race, channel)

    async def _get_active_race(self, ctx, id):
        races = await Race.all()
        ongoing_races = list(filter(lambda r: r.finished == False, races))
        if not id:
            if len(ongoing_races) == 0:
                await ctx.reply(_('There is currently no race ongoing'))
                return
            id = ongoing_races[-1].id
        races = list(filter(lambda r: r.id == id, ongoing_races))
        return races[0]

    @commands.group(
        brief=_('Join a race game.'),
        help=_('Join a race game.'),
        invoke_without_command=True,
        aliases=['enter']
    )
    async def join(self, ctx, id=None):
        # Check if the channel id is valid
        guild_settings = await GuildSettings.filter(guild=ctx.guild.id).first()
        if ctx.message.channel.id != guild_settings.race_registration_channel_id:
            return

        race = await self._get_active_race(ctx, id)
        if await Participant.filter(race=race, player_id=ctx.author.id).first():
            await ctx.reply(_('You already join an game.'))
            return
        try:
            participant = await Participant.create(race=race, player_id=ctx.author.id, player=ctx.author.name)
            await ctx.reply(
                _('You join the race from ') + f"{race.author}" + _(" with the preset ") + f"'{race.preset}'")
            # Add active racer role
            roles = list(filter(lambda r: r.id == guild_settings.race_active_role, ctx.guild.roles))
            await ctx.author.add_roles(*roles)
            race_channel = self.bot.get_guild(race.guild).get_channel(guild_settings.race_channel_id)
            await race_channel.send(f"# {ctx.author.name} " + _('joined the race.'))
            return
        except tortoise.exceptions.IntegrityError:
            await ctx.reply(_('You already join an game.'))

    @commands.group(
        brief=_('Join a race game.'),
        help=_('Join a race game.'),
        invoke_without_command=True
    )
    async def leave(self, ctx, id=None):
        # Check if the channel id is valid
        guild_settings = await GuildSettings.filter(guild=ctx.guild.id).first()
        if ctx.message.channel.id != guild_settings.race_registration_channel_id:
            return

        race = await self._get_active_race(ctx, id)
        if race.open:
            participant = await Participant.filter(race=race, player_id=ctx.author.id).first()
            if participant:
                await participant.delete()
                await ctx.reply(_('You left the race.'))
                # Remove active racer role
                roles = list(filter(lambda r: r.id == guild_settings.race_active_role, ctx.guild.roles))
                await ctx.author.remove_roles(*roles)
                race_channel = self.bot.get_guild(race.guild).get_channel(guild_settings.race_channel_id)
                messages = await race_channel.history().flatten()
                for message in messages:
                    if message.content.startswith(f"# {ctx.author.name}"):
                        await message.delete()
                        break
            else:
                await ctx.reply(_('You not joined any game.'))
        else:
            await ctx.reply(_('You can not leave a game with a nearly stated game.'))

    async def _chenge_role(self, author, roles, guild_settings):
        race_active = list(filter(lambda r: r.id == guild_settings.race_active_role, roles))[0]
        race_finished = list(filter(lambda r: r.id == guild_settings.race_finish_role, roles))[0]
        await author.remove_roles(race_active)
        await author.add_roles(race_finished)

    @commands.group(
        brief=_('You leave an ongoing match'),
        help=_('You leave an ongoing match.'),
        invoke_without_command=True,
        aliases=['ff']
    )
    async def cancel(self, ctx):
        # Check if the channel id is valid
        guild_settings = await GuildSettings.filter(guild=ctx.guild.id).first()
        if ctx.message.channel.id != guild_settings.race_channel_id:
            return

        race = await self._get_active_race(ctx, None)
        if (not race.ongoing and race.open) or race.finished:
            await ctx.reply(_("You can not be cancel an game, if it is not started."))
            return

        participant = await Participant.filter(race=race, player_id=ctx.author.id).first()
        if not participant.resign:
            participant.resign = True
            await participant.save()
            await self._chenge_role(ctx.author, ctx.guild.roles, guild_settings)
        await ctx.message.delete()

    async def _check_participants(self, race):
        # Check a race on all participants
        participants = await Participant.filter(race=race).all()
        race_finished = True
        for p in participants:
            if not p.resign:
                if not p.end_time:
                    race_finished = False
                    break
            else:
                race_finished = False
        if race_finished:
            await self._stop_race(race)
        return race_finished

    @commands.group(
        brief=_('Finish the game.'),
        help=_('Finish the game.'),
        invoke_without_command=True
    )
    async def done(self, ctx):
        # Check if the channel id is valid
        guild_settings = await GuildSettings.filter(guild=ctx.guild.id).first()
        if ctx.message.channel.id != guild_settings.race_channel_id:
            return

        race = await self._get_active_race(ctx, None)
        if not race.ongoing:
            await ctx.reply(_("You can not be finishing an game, if it is not started."))
            return
        participant = await Participant.filter(race=race, player_id=ctx.author.id).first()
        participant.end_time = datetime.datetime.now(self.tz)
        participant.time = participant.end_time - race.date
        await participant.save()
        await self._chenge_role(ctx.author, ctx.guild.roles, guild_settings)
        await ctx.message.delete()

        finished = await self._check_participants(race)
        if finished:
            await self._result(race, ctx.message.channel)


def setup(bot):
    bot.add_cog(AlttprRace(bot))
