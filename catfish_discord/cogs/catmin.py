from discord.ext import commands
from models.models import GuildSettings
import gettext
import os
import asyncio
import time

translate = gettext.translation('catfishbot', localedir='locale', fallback=True, languages=[os.getenv('LANG')])
_ = translate.gettext


class Catmin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def setup(self, ctx):
        if ctx.invoked.subcommand is None:
            await self.bot.say(_("Invalid command, please use subcommands."))

    async def _get_message_response(self, guild_id, channel_id, last_message, author_id):
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id)

        timeout = time.time() + 30
        while True:
            async for message in channel.history(after= last_message):
                if message.author.id == author_id:
                    return message
            if time.time() > timeout:
                break
        return None

    async def _abort_process(self, ctx, message, message_list):
        if message is not None:
            channel_id = message.content
            channel = ctx.guild.get_channel(channel_id)
            #if channel is not None:
            #    return False
            return False

        if message:
            await message.delete()
        for m in message_list:
            await m.delete()
        await ctx.send(_("No response or no valid channel was found. Please start the process again."))
        return True



    @setup.command(
        brief=_('Setup ids for discord server.'),
        help=_('Setup ids for discord server.'),
        invoke_without_command=True
    )
    @commands.has_permissions(administrator=True)
    async def race(self, ctx):
        message_list = list()
        message_list.append(ctx.message)

        author_id = ctx.message.author.id
        question_message = await ctx.send(_("Please enter the registration channel id:"))
        message_list.append(question_message)

        message = await self._get_message_response(ctx.guild.id, ctx.channel.id, question_message, author_id)
        if await self._abort_process(ctx, message, message_list):
            return
        registration_channel = message.content
        message_list.append(message)

        question_message = await ctx.send(_("Please enter the chat channel id:"))
        message_list.append(question_message)

        message = await self._get_message_response(ctx.guild.id, ctx.channel.id, question_message, author_id)
        if await self._abort_process(ctx, message, message_list):
            return
        chat_channel = message.content
        message_list.append(message)

        question_message = await ctx.send(_("Please enter the race channel id:"))
        message_list.append(question_message)

        message = await self._get_message_response(ctx.guild.id, ctx.channel.id, question_message, author_id)
        if await self._abort_process(ctx, message, message_list):
            return
        race_channel = message.content
        message_list.append(message)

        question_message = await ctx.send(_("Please enter the result channel id:"))
        message_list.append(question_message)

        message = await self._get_message_response(ctx.guild.id, ctx.channel.id, question_message, author_id)
        if await self._abort_process(ctx, message, message_list):
            return
        result_channel = message.content
        message_list.append(message)

        question_message = await ctx.send(_("Please enter the active race role id:"))
        message_list.append(question_message)

        message = await self._get_message_response(ctx.guild.id, ctx.channel.id, question_message, author_id)
        if await self._abort_process(ctx, message, message_list):
            return
        active_role = message.content
        message_list.append(message)

        question_message = await ctx.send(_("Please enter the finish race role id:"))
        message_list.append(question_message)

        message = await self._get_message_response(ctx.guild.id, ctx.channel.id, question_message, author_id)
        if await self._abort_process(ctx, message, message_list):
            return
        finish_role = message.content
        message_list.append(message)

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

        await ctx.message.channel.send(_("Setup done."))
        for m in message_list:
            await m.delete()


def setup(bot):
    bot.add_cog(Catmin(bot))
