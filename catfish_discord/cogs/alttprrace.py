import asyncio
import datetime
import gettext
import os

import pytz
from discord.ext import commands

from catfish_discord.util.alttpr import get_preset
from catfish_discord.util.alttpr_disord import get_embed
from models.models import Race, Participant, GuildSettings

translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext
tz = pytz.timezone(os.getenv("TIMEZONE", 'Europe/Berlin'))
emojis_guild_id = os.getenv("EMOJIS_GUILD_ID", 859817345743978497)


class AlttprRace(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._tasks = dict()
        asyncio.get_event_loop().create_task(self._create_tasks())

    async def _create_tasks(self):
        await asyncio.sleep(5)
        races = await Race.filter(finished=False).all().select_related('guild')
        for race in races:
            print(f"Race {race.id} is again stated.")
            task = asyncio.create_task(self._start_race(race))
            self._tasks[race.id] = task

    async def _start_race(self, race):
        guild = self.bot.get_guild(race.guild.id)
        channel = guild.get_channel(race.guild.race_channel_id)
        registration_channel = guild.get_channel(race.guild.race_registration_channel_id)
        delta = (race.date - datetime.datetime.now(tz)) - datetime.timedelta(minutes=10)
        if delta.total_seconds() > 0:
            await asyncio.sleep(delta.total_seconds())
            await registration_channel.send(_("== Registration is now closed, and race will start in 10 minutes. =="))
        else:
            await channel.send(_("Bot is crashed and will start the game in 10 minutes."))

        # Close registration
        race.open = False
        await race.save()

        # Generate new seed
        await channel.send(
            _("This is the seed for the upcoming race. If you finish the race, please enter !done in this channel."))
        seed = await get_preset(race.preset, hints=False, spoilers="off", allow_quickswap=True)
        emojis = self.bot.get_guild(emojis_guild_id).emojis
        embed = await get_embed(emojis, seed)
        await channel.send(embed=embed)
        race.seed = seed.url
        await race.save()

        # Countdown
        await channel.send(_("- Race will start in 10 minutes -"))
        await asyncio.sleep(300)
        await channel.send(_("- Race will start in 5 minutes -"))
        await asyncio.sleep(240)
        await channel.send(_("- Race will start in 1 minute -"))
        await asyncio.sleep(30)
        await channel.send(_("- Race will start in 30 seconds -"))
        await asyncio.sleep(20)
        await channel.send(_("- Race will start in 10 seconds -"))
        await asyncio.sleep(5)
        await channel.send(_("- Race will start in 5 seconds -"))
        await asyncio.sleep(1)
        await channel.send(_("- Race will start in 4 seconds -"))
        await asyncio.sleep(1)
        await channel.send(_("- Race will start in 3 seconds -"))
        await asyncio.sleep(1)
        await channel.send(_("- Race will start in 2 seconds -"))
        await asyncio.sleep(1)
        await channel.send(_("- Race will start in 1 second -"))
        await asyncio.sleep(1)
        await channel.send("========================")
        await channel.send(_("- Race is started! Good luck -"))
        await channel.send("========================")
        # Start game
        race.ongoing = True
        await race.save()
        await self._result_header(race)

    async def _remove_all_roles(self, participant):
        race = participant.race
        guild = self.bot.get_guild(race.guild.id)
        roles = list(filter(lambda r: r.id == race.guild.race_active_role
                                      or r.id == race.guild.race_finish_role, guild.roles))
        member = guild.get_member(participant.player_id)
        await member.remove_roles(*roles)

    async def _cleanup(self, race, ongoing):
        if ongoing:
            await asyncio.sleep(1800)
        guild = self.bot.get_guild(race.guild.id)
        participants = await Participant.filter(race=race).all().select_related("race", "race__guild")
        for p in participants:
            await self._remove_all_roles(p)
        channels = [
            guild.get_channel(race.guild.race_channel_id),
            guild.get_channel(race.guild.race_registration_channel_id),
            guild.get_channel(race.guild.race_result_channel_id)
        ]
        for channel in channels:
            messages = await channel.history().flatten()
            for message in messages:
                await message.delete()

    async def _stop_race(self, race):
        task = self._tasks[race.id]
        try:
            task.cancel()
            await task
        except:
            print("Exception ocurred")

        del self._tasks[race.id]

        # Remove roles
        asyncio.create_task(self._cleanup(race, race.ongoing))

        race.ongoing = False
        race.finished = True
        await race.save()

    async def _result_header(self, race, channel_id=None):
        channel_id = race.guild.race_result_channel_id if not channel_id else channel_id
        channel = self.bot.get_guild(race.guild.id).get_channel(channel_id)
        await channel.send(f"======== Race {race.id}  -  {race.preset} ========")
        await channel.send(f"Seed: {race.seed}")

    async def _result_participant(self, channel_id, count, player):
        race = player.race
        channel_id = race.guild.race_result_channel_id if not channel_id else channel_id
        channel = self.bot.get_guild(race.guild.id).get_channel(channel_id)
        time = "None" if player.time > datetime.timedelta(days=1) or player.resign else f"{player.time}"
        await channel.send(f"#{count} - {player.player} - Time: {time}")

    async def _result(self, race, channel_id=None):
        channel_id = race.guild.race_result_channel_id if not channel_id else channel_id
        await self._result_header(race, channel_id)
        channel = self.bot.get_guild(race.guild.id).get_channel(channel_id)

        participants = await Participant.filter(race=race).select_related("race", "race__guild").order_by('time')
        count = 1
        for player in participants:
            await self._result_participant(channel_id, count, player)
            count = count + 1

    async def _get_active_race(self, ctx):
        active_race = await Race.get_or_none(finished=False, guild__id=ctx.guild.id).select_related("guild")
        if not active_race:
            await ctx.message.channel.send(_('There is currently no race ongoing'))
        return active_race

    async def _change_role(self, participant):
        guild = self.bot.get_guild(participant.race.guild.id)
        member = guild.get_member(participant.player_id)
        race_active = list(filter(lambda r: r.id == participant.race.guild.race_active_role, guild.roles))[0]
        race_finished = list(filter(lambda r: r.id == participant.race.guild.race_finish_role, guild.roles))[0]
        await member.remove_roles(race_active)
        await member.add_roles(race_finished)

    async def _check_participants(self, race):
        # Check a race on all participants
        active_runner_count = await Participant.filter(race=race, done=False, resign=False).count()
        race_finished = active_runner_count == 0
        if race_finished:
            await self._stop_race(race)
            #await self._result
            resign_players = await Participant.filter(race=race, resign=True).select_related("race", "race__guild")
            position = await Participant.filter(race=race, done=True).count() + 1
            for rp in resign_players:
                await self._result_participant(None, position, rp)

    async def _check_channel(self, ctx, channel_type):
        guild_settings = await GuildSettings.get(id=ctx.guild.id)
        if channel_type == 'registration':
            return ctx.message.channel.id == guild_settings.race_registration_channel_id
        elif channel_type == 'active':
            return ctx.message.channel.id == guild_settings.race_channel_id
        else:
            return False

    @commands.group(pass_context=True, invoke_without_command=True)
    async def race(self, ctx):
        if ctx.invoked.subcommand is None:
            await self.bot.say(_("Invalid command, please use subcommands."))

    @race.command(
        brief=_('Start a new race game.'),
        help=_('Start a new race game.'),
        invoke_without_command=True,
        pass_context=True
    )
    async def start(self, ctx, time, preset):
        # Check if the channel id is valid
        if not await self._check_channel(ctx, 'registration'):
            return

        now = datetime.datetime.now(tz)
        race_time = datetime.datetime.strptime(time, '%H:%M')
        start_time = now.replace(hour=race_time.hour, minute=race_time.minute, second=0)
        delta = start_time - now

        # Check for starting time
        if delta < datetime.timedelta(minutes=10):
            await ctx.reply(_("Please start a race game more then 10 minutes before."))
            return

        # Check if user already started a race
        race = await Race.get_or_none(author_id=ctx.author.id, finished=False)
        if race:
            await ctx.reply(
                _('Please finish your old race before you start a new one. Race ID: ') + f"{race.id}")
            return

        # Check if already a race is started in guild
        active_guild_races = await Race.filter(guild__id=ctx.guild.id, finished=False).count()
        if active_guild_races > 0:
            await ctx.reply(_('There is already a race ongoing, you cannot start a new one.'))
            return

        # Create race
        guild_settings = await GuildSettings.get(id=ctx.guild.id)
        race = await Race.create(preset=preset, author_id=ctx.author.id,
                                 author=ctx.author.display_name, date=start_time,
                                 guild=guild_settings)

        task = asyncio.create_task(self._start_race(race))
        self._tasks[race.id] = task

        # Private Message
        await ctx.author.send(_('New race is generated. Race ID: ') + f"{race.id}")

        # Public Message
        await ctx.message.channel.send(
            _('New race is planned. - Race ID: ') + f"{race.id} -" + _("The race will be start at ") + f"{time} - "
            + _("Registration is possible until 10 minutes before the start time"))
        await ctx.message.channel.send(
            _('Enter the command !joint to join the race. Enter !leave if you want to leave the race again.'))
        await ctx.message.channel.send('====================================')
        await ctx.message.channel.send(_("Participants:"))

        # todo Random Message

    @race.command(
        brief=_('Stop a race game.'),
        help=_('Stop a race game.'),
        invoke_without_command=True,
        pass_context=True
    )
    async def stop(self, ctx, race_id=None):
        # Check if the channel id is valid
        if not await self._check_channel(ctx, 'registration'):
            return

        if race_id:
            race = await Race.get_or_none(id=race_id, finished=False).select_related("guild")
        else:
            race = await Race.get_or_none(author_id=ctx.author.id, finished=False).select_related("guild")

        if race:
            await self._stop_race(race)
            await ctx.reply(_('You stopped the race with id: ') + f"{race.id}")
        else:
            await ctx.reply(_('There is no active race from you or with this ID.'))

    @race.command(
        brief=_('Get the result of an race.'),
        help=_('Get the result of an race.'),
        invoke_without_command=True,
        pass_context=True
    )
    async def result(self, ctx, race_id):
        race = await Race.get_or_none(id=race_id).select_related("guild")
        if race:
            await self._result(race, ctx.message.channel.id)

    @commands.group(
        brief=_('Join a race game.'),
        help=_('Join a race game.'),
        invoke_without_command=True,
        aliases=['enter']
    )
    async def join(self, ctx):
        # Check if the channel id is valid
        if not await self._check_channel(ctx, 'registration'):
            return

        race = await self._get_active_race(ctx)
        if race:
            participant_tuple = await Participant.get_or_create(race=race, player_id=ctx.author.id,
                                                                player=ctx.author.display_name)
            if not participant_tuple[1]:
                await ctx.reply(_('You already join an game.'))
                return
            else:
                roles = list(filter(lambda r: r.id == race.guild.race_active_role, ctx.guild.roles))
                await ctx.author.add_roles(*roles)
                await ctx.message.channel.send(f"# **{ctx.author.display_name}** " + _('joined the race.'))
        await ctx.message.delete()

    @commands.group(
        brief=_('Leave a race game.'),
        help=_('Leave a race game.'),
        invoke_without_command=True
    )
    async def leave(self, ctx):
        # Check if the channel id is valid
        if not await self._check_channel(ctx, 'registration'):
            return

        race = await self._get_active_race(ctx)
        if race:
            if race.open:
                participant = await Participant.get_or_none(race=race, player_id=ctx.author.id).select_related(
                    'race', 'race__guild')
                if participant:
                    await self._remove_all_roles(participant)
                    await participant.delete()

                    # Remove from list
                    messages = await ctx.message.channel.history().flatten()
                    for message in messages:
                        if message.content.startswith(f"# **{ctx.author.display_name}**"):
                            await message.delete()
                            break
                else:
                    await ctx.message.channel.send(_('You not joined any game.'))
            else:
                await ctx.message.channel.send(_('You can not leave a game with a nearly started or ongoing.'))
        await ctx.message.delete()

    @commands.group(
        brief=_('You leave an ongoing match.'),
        help=_('You leave an ongoing match.'),
        invoke_without_command=True,
        aliases=['ff']
    )
    async def cancel(self, ctx):
        # Check if the channel id is valid
        if not await self._check_channel(ctx, 'active'):
            return

        race = await self._get_active_race(ctx)
        if race:
            if race.ongoing:
                await ctx.reply(_("You can not be cancel an game, if it is not started."))
            else:
                participant = await Participant.get_or_none(race=race, player_id=ctx.author.id).select_related(
                        "race", "race__guild")
                if participant and not participant.resign:
                    participant.resign = True
                    participant.done = True
                    await participant.save()
                    await self._change_role(participant)
                    asyncio.create_task(self._check_participants(race))

        await ctx.message.delete()

    @commands.group(
        brief=_('Finish the game.'),
        help=_('Finish the game.'),
        invoke_without_command=True
    )
    async def done(self, ctx):
        # Check if the channel id is valid
        if not await self._check_channel(ctx, 'active'):
            return

        race = await self._get_active_race(ctx)
        if race:
            if not race.ongoing:
                await ctx.reply(_("You can not be finishing an game, if it is not started."))
            else:
                participant = await Participant.get_or_none(race=race, player_id=ctx.author.id).select_related(
                    "race", "race__guild")
                if participant and not participant.resign and not participant.done:
                    participant.end_time = datetime.datetime.now(tz)
                    participant.time = participant.end_time - race.date
                    participant.done = True
                    await participant.save()
                    await self._change_role(participant)

                    # Write result after done
                    position = await Participant.filter(race=race, done=True).count()
                    await self._result_participant(None, position, participant)

                    # Check if race is finished
                    asyncio.create_task(self._check_participants(race))

        await ctx.message.delete()


def setup(bot):
    bot.add_cog(AlttprRace(bot))
