"""Various settings handlers."""

import discord


async def accessibility(ctx: discord.ApplicationContext) -> bool:
    """Whether to use accessibility mode for the current operation."""
    return False  # TODO: Implement!


async def use_emojis(ctx: discord.ApplicationContext) -> bool:
    """Whether to use emojis."""
    return not await accessibility(ctx)
