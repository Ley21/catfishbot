import os
from discord.ext import commands
from catfish_discord.util.alttpr import get_preset, get_mystery, get_multiworld
from catfish_discord.util.alttpr_disord import get_embed
import gettext
import requests

translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext


class AlttprDefault(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        brief=_('Generate a seed from preset.'),
        help=_('Generate a seed from preset.'),
        invoke_without_command=True
    )
    async def seed(self, ctx, preset, hints=False):

        seed = await get_preset(preset, hints=hints, spoilers="on", allow_quickswap=True)

        emojis = ctx.guild.emojis
        embed = await get_embed(emojis, seed)
        await ctx.reply(embed=embed)

    @commands.group(
        brief=_('Generate a seed from preset without an spoiler log.'),
        help=_('Generate a seed from preset without an spoiler log.'),
        invoke_without_command=True
    )
    async def nospoiler(self, ctx, preset, hints=False):
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


def setup(bot):
    bot.add_cog(AlttprDefault(bot))
