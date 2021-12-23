import os
from distutils.util import strtobool
from disnake.ext import commands
from catfish_discord.util.alttpr import get_preset, generate_mystery_game, get_multiworld
from catfish_discord.util.alttpr_disord import get_embed
import gettext
import requests
from catfish_discord.util.alttpr_extensions import write_progression_spoiler
import base64
from models.models import GameConfiguration


translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext
emojis_guild_id = os.getenv("EMOJIS_GUILD_ID", 859817345743978497)


class AlttprDefault(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        description=_('Generate a seed from preset.'),
    )
    async def spoiler(self, ctx, preset, hints=False):
        await ctx.response.defer()
        seed = await get_preset(preset, hints=hints, spoilers="on", allow_quickswap=True)
        if seed:
            emojis = self.bot.get_guild(emojis_guild_id).emojis
            embed = await get_embed(emojis, seed)
            optimize_spoiler = strtobool(os.getenv("OPTIMIZE_SPOILER", "true"))
            if optimize_spoiler:
                spoiler_link = await write_progression_spoiler(seed)
                embed.insert_field_at(0, name="Spoiler Log URL", value=spoiler_link, inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(_("Seed could not be generated. Hint: Door randomizer are currently not working"))
            return

    @commands.slash_command(
        description=_('Generate a seed from preset without an spoiler log.'),
    )
    async def seed(self, ctx, preset, hints=False):
        await ctx.response.defer()
        seed = await get_preset(preset, hints=hints, spoilers="off", allow_quickswap=True)
        if seed:
            emojis = self.bot.get_guild(emojis_guild_id).emojis
            embed = await get_embed(emojis, seed)
            await ctx.send(embed=embed)
        else:
            await ctx.send(_("Seed could not be generated. Hint: Door randomizer are currently not working"))
            return

    @commands.slash_command(
        description=_('Generate a mystery seed.')
    )
    async def mystery(self, ctx, preset='weighted'):
        await ctx.response.defer()
        seed = await generate_mystery_game(preset)
        if seed:
            emojis = self.bot.get_guild(emojis_guild_id).emojis
            embed = await get_embed(emojis, seed)
            await ctx.send(embed=embed)
        else:
            await ctx.send(_("Seed could not be generated. Hint: Door randomizer are currently not working"))
            return

    @commands.command(
        brief=_('Generate a multiworld game.'),
        help=_('Generate a multiworld game.'),
        invoke_without_command=True
    )
    async def multi(self, ctx):
        await ctx.reply(_("Catfishbot prepare the party room for mutli world..."))
        multi = {}
        try:
            if len(ctx.message.attachments) > 0:
                attachment_url = ctx.message.attachments[0].url
                file_request = requests.get(attachment_url)
                multi = await get_multiworld(file_request.content)
        except:
            multi = None

        if multi is None:
            await ctx.send(_('Multiworld could not be generated.'))
        else:
            if multi['error'] != '':
                await ctx.send(_('Multiworld could not be generated.'))
                await ctx.send(multi['error'])
            else:
                await ctx.author.send(_('Multiworld Seed Information') + f": {multi['seed_info_url']}")
                await ctx.send(_('Multiworld Room') + f": {multi['room_url']}")

    @commands.slash_command(
        description=_('Generate a mystery seed.')
    )
    async def multiworld(self, inter, users):
        await inter.response.defer()
        user_id_list = []
        user_name_list = users.split(',')
        async for member in inter.guild.fetch_members():
            if member.display_name in user_name_list:
                user_id_list.append(member.id)
        configurations = []
        for user_id in user_id_list:
            user_game_config = await GameConfiguration.get_or_none(user_id=user_id).select_related()
            yaml = base64.b64decode(user_game_config.config_file)
            configurations.append(yaml)
        # todo multiworld by yaml from database
        await inter.send("fluff")

    @commands.command(
        brief=_('Save an multi world yaml file for an user'),
        help=_('Save an multi world yaml file for an user'),
        invoke_without_command=True
    )
    async def yaml(self, ctx, game, username=None):
        if username is not None:
            for member in ctx.guild.members:
                if member.display_name == username:
                    user_id = member.id
                    break
        else:
            user_id = ctx.author.id
        if not validate_game(game):
            await ctx.send(_('No valid game was send. (e.g. alttp, oot)'))
        if len(ctx.message.attachments) > 0:
            try:
                attachment_url = ctx.message.attachments[0].url
                file_request = requests.get(attachment_url)
                yaml_file_base64 = str(base64.b64encode(file_request.content), "utf-8")
                if yaml_file_base64 != "":
                    config = await GameConfiguration.get_or_none(user_id=user_id, game=game).select_related()
                    if config is None:
                        await GameConfiguration.create(user_id=user_id,game=game,config_file=yaml_file_base64)
                    else:
                        config.config_file = yaml_file_base64
                        await config.save()
                    await ctx.reply(_("Your configuration was saved."))
            except:
                await ctx.send(_('File could not be parsed.'))
        else:
            await ctx.send(_('File could not be found.'))


def validate_game(game):
    if game == 'alttp':
        return True
    elif game == 'oot':
        return True
    else:
        return False


def setup(bot):
    bot.add_cog(AlttprDefault(bot))
