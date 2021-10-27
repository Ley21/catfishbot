from discord.ext import commands
from models.models import GuildSettings
import gettext
import os

translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext


class Catmin(commands.Cog):

    @commands.group(
        brief=_('Setup ids for discord server.'),
        help=_('Setup ids for discord server.'),
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, registration_channel, chat_channel, race_channel,
                    result_channel, active_role, finish_role):
        dev_guild_settings = {
            "id": ctx.guild.id,
            "race_registration_channel_id": registration_channel,
            "race_chat_channel_id": chat_channel,
            "race_channel_id": race_channel,
            "race_result_channel_id": result_channel,
            "race_active_role": active_role,
            "race_finish_role": finish_role
        }
        await GuildSettings.update_or_create(dev_guild_settings)

        await ctx.reply(_("Setup done."))
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Catmin(bot))
