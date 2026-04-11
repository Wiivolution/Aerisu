from __future__ import annotations

import asyncio
import datetime
import discord
import re
import random

from collections import deque
from discord.ext import commands
from string import printable
from subprocess import call
from typing import TYPE_CHECKING
from utils.checks import check_staff
from utils.configuration import KillBoxState
from utils.utils import send_dm_message, gen_color
from utils import Restriction
from utils.database import FilterKind
from utils.views.generic import ignored_file_extensions

if TYPE_CHECKING:
    from kurisu import Kurisu
    from typing import Deque


class Events(commands.Cog):
    """
    Special event handling.
    """

    def __init__(self, bot: Kurisu):
        self.bot: Kurisu = bot
        self.configuration = bot.configuration
        self.filters = self.bot.filters
        self.restrictions = self.bot.restrictions

    # I hate naming variables sometimes
    user_ping_antispam: dict[int, Deque[tuple[discord.Message, int]]] = {}
    user_message_antispam: dict[int, list[discord.Message]] = {}
    userbot_yeeter: dict[int, list[discord.abc.MessageableChannel]] = {}

    async def userbot_yeeter_pop(self, message: discord.Message):
        await asyncio.sleep(40)
        self.userbot_yeeter[message.author.id].remove(message.channel)
        try:
            if len(self.userbot_yeeter[message.author.id]) == 0:
                self.userbot_yeeter.pop(message.author.id)
        except KeyError:
            pass

    async def invite_spam_pop(self, message: discord.Message):
        await asyncio.sleep(40)
        self.invite_antispam[message.author.id].remove(message)
        try:
            if len(self.userbot_yeeter[message.author.id]) == 0:
                self.userbot_yeeter.pop(message.author.id)
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot or message.type is discord.MessageType.auto_moderation_action:
            return
        if not self.bot.IS_DOCKER:
            if message.author.name == "GitHub" and message.author.discriminator == "0000":
                if message.embeds and message.embeds[0].title and message.embeds[0].title.startswith('[Kurisu:port]'):
                    await self.bot.channels['bot-dev'].send("Automatically pulling changes!")
                    call(['git', 'pull'])
                    await self.bot.channels['bot-dev'].send("Restarting bot...")
                    await self.bot.close()
                return
        await self.bot.wait_until_all_ready()
        if message.author == message.guild.me or check_staff(self.bot, 'Moderator', message.author.id) \
                or message.channel.id in self.bot.configuration.nofilter_list:
            return
        if db_chan := await self.bot.configuration.get_channel(message.channel.id):
            match db_chan.killbox_state:
                case KillBoxState.Kick:
                    try:
                        mes = await self.bot.logs.post_message_log(":envelope: **Message posted**",
                                                                   f"{message.author.mention} posted a message in killbox {message.channel.mention}",
                                                                   message.content)
                        self.bot.actions.append(f'wk:{message.author.id}')
                        await message.author.kick(reason=f"Kill box automated Action. See {mes.jump_url}")
                        await message.delete()
                    except discord.Forbidden:
                        self.bot.actions.remove(f'wk:{message.author.id}')
                    return
                case KillBoxState.Ban:
                    try:
                        mes = await self.bot.logs.post_message_log(":envelope: **Message posted**",
                                                                   f"{message.author.mention} posted a message in killbox {message.channel.mention}",
                                                                   message.content)
                        self.bot.actions.append(f"wb:{message.author.id}")
                        await message.author.ban(reason=f"Automated Action. See {mes.jump_url}", delete_message_days=1)
                    except discord.Forbidden:
                        self.bot.actions.remove(f'wb:{message.author.id}')
                    return
                case KillBoxState.Probate:
                    try:
                        await self.restrictions.add_restriction(message.author, Restriction.Probation, f"Posted a message in killbox {message.channel.mention}")
                        mes = await self.bot.logs.post_message_log(":envelope: **Message posted**",
                                                                   f"{message.author.mention} posted a message in killbox {message.channel.mention}",
                                                                   message.content)
                        await message.delete();
                    except discord.Forbidden:
                        self.bot.actions.remove(f'wk:{message.author.id}')
        # await self.scan_message(message) replaced by automod
        # self.bot.loop.create_task(self.user_ping_check(message)) replaced by automod
        # self.bot.loop.create_task(self.user_spam_check(message)) replaced by automod
        # self.bot.loop.create_task(self.channel_spam_check(message)) replaced by automod

    @commands.Cog.listener()
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message):
        if message_after.guild is None or message_after.author.bot:
            return
        await self.bot.wait_until_all_ready()
        if message_after.author == message_after.guild.me or check_staff(self.bot, 'Moderator', message_after.author.id) \
                or message_after.channel.id in self.bot.configuration.nofilter_list:
            return
        if message_before.content == message_after.content:
            return
        # await self.scan_message(message_after, is_edit=True) replaced by automod


async def setup(bot):
    await bot.add_cog(Events(bot))
