from __future__ import annotations

import discord

from discord.ext import commands
from typing import TYPE_CHECKING
from utils import StaffRank, OptionalMember
from utils.checks import is_staff

if TYPE_CHECKING:
    from kurisu import Kurisu
    from utils.context import KurisuContext, GuildContext


class ModStaff(commands.Cog):
    """
    Staff management commands.
    """

    def __init__(self, bot: Kurisu):
        self.bot: Kurisu = bot
        self.emoji = discord.PartialEmoji.from_str('🛠️')
        self.configuration = self.bot.configuration

    async def cog_check(self, ctx: KurisuContext):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @is_staff("Owner")
    @commands.command()
    async def addstaff(self, ctx: GuildContext, member: discord.Member | discord.User, position: str):
        """Add user as staff. Owners only."""
        if position not in self.bot.staff_roles:
            await ctx.send(f"💢 That's not a valid position. You can use __{'__, __'.join(self.bot.staff_roles.keys())}__")
            return
        res = await self.bot.configuration.add_staff(member, position)
        if not res:
            return await ctx.send("Failed to add staff member.")
        await self.bot.configuration.update_staff_roles(member)
        await ctx.send(f"{member.mention} is now on staff as {position}. Welcome to the secret party room!")

    @is_staff("Owner")
    @commands.command()
    async def delstaff(self, ctx: GuildContext, member: discord.Member | discord.User):
        """Remove user from staff. Owners only."""
        await ctx.send(member.name)
        res = await self.bot.configuration.delete_staff(member)
        if not res:
            return await ctx.send("Failed to remove staff member.")
        await self.bot.configuration.update_staff_roles(member)
        await ctx.send(f"{member.mention} is no longer staff. Stop by some time!")

    @commands.command()
    async def liststaff(self, ctx: GuildContext):
        """List staff members per rank."""
        ranks: dict[str, list] = {}
        embed = discord.Embed()
        for rank in self.bot.staff_roles.keys():
            ranks[rank] = []
            for user_id, staff_rank in self.configuration.staff.items():
                if rank == staff_rank.name:
                    ranks[rank].append(user_id)
            if ranks[rank]:
                embed.add_field(
                    name=rank,
                    value="".join(f"<@{x}>\n" for x in ranks[rank]),
                    inline=False,
                )

        await ctx.send("Here is a list of our staff members:", embed=embed)


async def setup(bot):
    await bot.add_cog(ModStaff(bot))
