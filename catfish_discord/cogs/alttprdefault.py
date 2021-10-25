import os
import threading

import discord.ext.commands
from discord.ext import commands
from catfish_discord.util.alttpr import get_preset, get_mystery, get_multiworld
from catfish_discord.util.alttpr_disord import get_embed
import gettext
import requests
from catfish_discord.util.alttpr_extensions import write_progression_spoiler
from models.race import Race, Participant
import datetime
import tortoise


translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext


class AlttprDefault(commands.Cog):

    threads = list()

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        brief=_('Generate a seed from preset.'),
        help=_('Generate a seed from preset.'),
        invoke_without_command=True
    )
    async def spoiler(self, ctx, preset, hints=False):

        seed = await get_preset(preset, hints=hints, spoilers="on", allow_quickswap=True)
        spoiler_link = await write_progression_spoiler(seed)
        emojis = ctx.guild.emojis
        embed = await get_embed(emojis, seed)
        embed.insert_field_at(0, name="Spoiler Log URL",
                              value=spoiler_link, inline=False)
        await ctx.reply(embed=embed)

    @commands.group(
        brief=_('Generate a seed from preset without an spoiler log.'),
        help=_('Generate a seed from preset without an spoiler log.'),
        invoke_without_command=True
    )
    async def seed(self, ctx, preset, hints=False):
        seed = await get_preset(preset, hints=hints, spoilers="off", allow_quickswap=True)

        emojis = ctx.guild.emojis
        embed = await get_embed(emojis, seed)
        await ctx.reply(embed=embed)

    @commands.group(
        brief=_('Generate a mystery seed.'),
        help=_('Generate a mystery seed.'),
        invoke_without_command=True
    )
    async def mystery(self, ctx, preset='weighted'):
        seed = await get_mystery(preset)

        emojis = ctx.guild.emojis
        embed = await get_embed(emojis, seed)
        await ctx.reply(embed=embed)

    @commands.group(
        brief=_('Generate a multiworld game.'),
        help=_('Generate a multiworld game.'),
        invoke_without_command=True
    )
    async def multi(self, ctx):
        if len(ctx.message.attachments) > 0:
            attachment_url = ctx.message.attachments[0].url
            file_request = requests.get(attachment_url)
            multi = await get_multiworld(file_request.content)

            if multi is not None:
                await ctx.author.send(_('Multiworld Seed Information') + f": {multi['seed_info_url']}")
                await ctx.reply(_('Multiworld Room') + f": {multi['seed_info_url']}")
                return

        await ctx.reply(_('Multiworld could not be generated.'))

    @commands.group(
        brief=_('Create a race game.'),
        help=_('Create a race game.'),
        invoke_without_command=True
    )
    async def race(self, ctx, command, arg1=None, arg2=None, arg3=None):
        if command == 'start':
            # todo Anmeldung
            # todo eher als 10 min vorher
            if not arg1 or not arg2:
                await ctx.reply(_('Missing start time or preset'))
                return
            races = await Race.filter(author_id=ctx.author.id,ongoing=True).all()
            if len(races) > 0:
                await ctx.reply(_('Please finish you old race before you start a new one. Race ID: ' + f"{races[0].id}"))
                return

            # arg1 is time if start
            race_time = datetime.datetime.strptime(arg1, '%H:%M')
            start_time = datetime.datetime.today().replace(hour=race_time.hour, minute=race_time.minute, second=0)

            # arg2 is preset if start
            preset = arg2

            # Generate an game
            seed = await get_preset(preset, hints=False, spoilers="off", allow_quickswap=True)
            seed_id = seed.url.replace("https://alttpr.com/h/","")

            race = await Race.create(preset=preset, seed=seed_id, author_id=ctx.author.id, author=ctx.author.name, date=start_time)
            # delta_registration_close = (start_time - datetime.datetime.now()).total_seconds() - 600
            #
            # close = threading.Timer(delta_registration_close, lambda:
            # {
            #     await ctx.reply(_("Registration is closed."))
            #     # todo send seed
            #     todo countdown
            # })
            #
            # close.start()
            # self.threads.append(close)
            # todo: Send to creator id
            await ctx.reply(_('New race is generated. Race ID: ')+f"{race.id}")
        elif command == 'stop':
            # arg1 is race id
            if not arg1:
                race = await Race.filter(author_id=ctx.author.id, ongoing=True).first()
            else:
                race = await Race.filter(id=arg1).first()
            race.ongoing = False
            await race.save()
            await ctx.reply(_('You stopped the race with id: ') + f"{race.id}")
            # todo remove role after 30 min
        elif command == 'result':
            # todo race results
            print("ergebnisse")


    @commands.group(
        brief=_('Join a race game.'),
        help=_('Join a race game.'),
        invoke_without_command=True,
        aliases=['enter']
    )
    async def join(self, ctx, id=None):
        races = await Race.all()
        ongoing_races = list(filter(lambda r: r.ongoing, races))
        if not id:
            if len(ongoing_races) == 0:
                await ctx.reply(_('There is currently no race ongoing'))
                return
            id = ongoing_races[-1].id
        race = list(filter(lambda r: r.id == id, ongoing_races))[0]
        try:
            participant = await Participant.create(race=race, player_id=ctx.author.id, player=ctx.author.name)
            await ctx.reply(
                _('You join the race from ') + f"{race.author}" + _(" with the preset ") + f"'{race.preset}'")
        except tortoise.exceptions.IntegrityError:
            await ctx.reply(_('You already join the game.'))
        # todo racer role

    @commands.group(
        brief=_('Join a race game.'),
        help=_('Join a race game.'),
        invoke_without_command=True,
        aliases=['ff']
    )
    async def leave(self, ctx, id=None):
        # todo: remove from list, only if ongoing
        #
        print("das")

    @commands.group(
        brief=_('Join a race game.'),
        help=_('Join a race game.'),
        invoke_without_command=True
    )
    async def done(self, ctx):
        # todo: finish race role
        await ctx.message.delete()
        # todo: check if all have been finished -> close race
        # close ->

# race-anmeldung: id
# chat: id
# aktuelles_race: id
# race_ergebnis: id
# role_active_racer: id
# role_finish_race: id


def setup(bot):
    bot.add_cog(AlttprDefault(bot))
