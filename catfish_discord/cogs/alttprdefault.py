import os
from distutils.util import strtobool
from discord.ext import commands
from catfish_discord.util.alttpr import get_preset, generate_mystery_game, get_multiworld
from catfish_discord.util.alttpr_disord import get_embed
import gettext
import requests
from catfish_discord.util.alttpr_extensions import write_progression_spoiler


translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext
emojis_guild_id = os.getenv("EMOJIS_GUILD_ID", 859817345743978497)


class AlttprDefault(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        brief=_('Generate a seed from preset.'),
        help=_('Generate a seed from preset.'),
        invoke_without_command=True
    )
    async def spoiler(self, ctx, preset, hints=False):

        seed = await get_preset(preset, hints=hints, spoilers="on", allow_quickswap=True)
        if seed:
            emojis = self.bot.get_guild(emojis_guild_id).emojis
            embed = await get_embed(emojis, seed)
            optimize_spoiler = strtobool(os.getenv("OPTIMIZE_SPOILER", "true"))
            if optimize_spoiler:
                spoiler_link = await write_progression_spoiler(seed)
                embed.insert_field_at(0, name="Spoiler Log URL", value=spoiler_link, inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(_("Seed could not be generated. Hint: Door randomizer are currently not working"))
            return

    @commands.group(
        brief=_('Generate a seed from preset without an spoiler log.'),
        help=_('Generate a seed from preset without an spoiler log.'),
        invoke_without_command=True
    )
    async def seed(self, ctx, preset, hints=False):
        seed = await get_preset(preset, hints=hints, spoilers="off", allow_quickswap=True)
        if seed:
            emojis = self.bot.get_guild(emojis_guild_id).emojis
            embed = await get_embed(emojis, seed)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(_("Seed could not be generated. Hint: Door randomizer are currently not working"))
            return

    @commands.group(
        brief=_('Generate a mystery seed.'),
        help=_('Generate a mystery seed.'),
        invoke_without_command=True
    )
    async def mystery(self, ctx, preset='weighted'):
        seed = await generate_mystery_game(preset)
        if seed:
            emojis = self.bot.get_guild(emojis_guild_id).emojis
            embed = await get_embed(emojis, seed)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(_("Seed could not be generated. Hint: Door randomizer are currently not working"))
            return

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
                if multi['error'] != '':
                    await ctx.reply(_('Multiworld could not be generated.'))
                    await ctx.reply(multi['error'])
                    return
                await ctx.author.send(_('Multiworld Seed Information') + f": {multi['seed_info_url']}")
                await ctx.reply(_('Multiworld Room') + f": {multi['room_url']}")
                return

        await ctx.reply(_('Multiworld could not be generated.'))


def setup(bot):
    bot.add_cog(AlttprDefault(bot))
