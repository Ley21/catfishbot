import logging
from discord.ext import commands
from discord.ext.commands import errors

discord_bot = commands.Bot(
    command_prefix="!"
)

# noinspection SpellCheckingInspection
discord_bot.load_extension("catfish_discord.cogs.alttprdefault")


@discord_bot.event
async def on_command(ctx):
    await ctx.message.add_reaction('⌚')


@discord_bot.event
async def on_command_completion(ctx):
    await ctx.message.add_reaction('✅')
    await ctx.message.remove_reaction('⌚', ctx.bot.user)


@discord_bot.event
async def on_message(message):
    # override catfish_discord.py's process_commands coroutine in the commands.Bot class
    if message.author.bot:
        return

    ctx = await discord_bot.get_context(message)

    # replace the bots invoke coroutine a modified version
    # this allows the bot to begin "typing" when processing a command
    if ctx.command is not None:
        discord_bot.dispatch('command', ctx)
        try:
            if await discord_bot.can_run(ctx, call_once=True):
                async with ctx.typing():
                    await ctx.command.invoke(ctx)
            else:
                raise errors.CheckFailure(
                    'The global check once functions failed.')
        except errors.CommandError as exc:
            await ctx.command.dispatch_error(ctx, exc)
        else:
            discord_bot.dispatch('command_completion', ctx)


@discord_bot.event
async def on_command_error(ctx, error):
    await ctx.message.remove_reaction('⌚', ctx.bot.user)
    logging.info(error)
    if isinstance(error, commands.CheckFailure):
        pass
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.message.add_reaction('🚫')
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        error_to_display = error.original if hasattr(
            error, 'original') else error
        raise error_to_display
