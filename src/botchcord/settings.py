"""Various settings handlers."""

from bot import AppCtx


async def accessibility(ctx: AppCtx) -> bool:
    """Whether to use accessibility mode for the current operation."""
    guild = await ctx.bot.guild_cache.fetch(ctx.guild, create=True)
    if guild.settings.accessibility:
        return True

    user = await ctx.bot.user_store.fetch(ctx.author.id)
    return user.settings.accessibility


async def use_emojis(ctx: AppCtx) -> bool:
    """Whether to use emojis."""
    return not await accessibility(ctx)
