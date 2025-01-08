#!/usr/bin/env python3
import asyncio
import logging
import sys
from argparse import ArgumentParser, Namespace
from copy import deepcopy
from json import load
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtWidgets import QApplication
from discord import Intents, VoiceClient, TextChannel, Guild
from discord.ext import commands
from discord.ext.commands import Bot, Context, Cog
from qasync import QEventLoop

from .PhasedContext import PhasedContext
from .interface.main_window import MainWindow
from .session import BaseSession, BackgroundSession
from .ursa_config import INVITE_LINK

ursa_bot: Bot = Bot(
    command_prefix='>',
    description="Ursa Music Bot",
    intents=Intents.default()
)


class Ursa(Cog):
    bot: Bot
    sessions: Dict[Guild, BaseSession]
    ctx_groups: Dict[str, PhasedContext]

    def __init__(self, bot: Bot, config: Dict):
        self.bot = bot
        self.sessions = dict()
        self.ctx_groups = dict()
        for name, context_cfg in config.items():
            self.ctx_groups[name] = PhasedContext.from_dict(context_cfg)

    def get_session(self, guild: Guild) -> Optional[BaseSession]:
        return self.sessions.get(guild, None)

    def channel_is_valid(self, channel: TextChannel) -> bool:
        session: Optional[BaseSession] = self.get_session(channel.guild)
        if session is None:
            return False

        return channel == session.text_channel

    async def new_context(self, ctx: Context, context_name: str) -> BackgroundSession:
        vc: VoiceClient = await ctx.author.voice.node.connect()
        context: PhasedContext = deepcopy(self.ctx_groups[context_name])
        session = BackgroundSession(ctx.guild, context_name, context, vc, ctx.channel)
        self.sessions[ctx.guild] = session
        return session

    @commands.command()
    async def leave(self, ctx: Context):
        await ctx.message.delete()
        if not self.channel_is_valid(ctx.channel):
            return

        session: BaseSession = self.get_session(ctx.guild)
        print("DEBUG: -> command leave")
        session.stop()
        await ctx.voice_client.disconnect()
        del self.sessions[ctx.guild]

    @commands.command()
    async def stop(self, ctx: Context):
        await ctx.message.delete()
        if not self.channel_is_valid(ctx.channel):
            return

        print("DEBUG: -> command stop")
        session: BaseSession = self.get_session(ctx.guild)
        if session is None or not isinstance(session, BackgroundSession):
            # await ctx.channel.send("No Session.")
            return

        session.is_stopped = True
        vc = session.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()

        session.context.reset()

    @commands.command()
    async def pause(self, ctx: Context):
        await ctx.message.delete()
        if not self.channel_is_valid(ctx.channel):
            return

        session: Optional[BaseSession] = self.get_session(ctx.guild)
        if not isinstance(session, BackgroundSession):
            return
        print("DEBUG: -> command pause")
        vc = session.voice_client
        if vc and vc.is_playing():
            vc.pause()

    @commands.command()
    async def resume(self, ctx: Context):
        await ctx.message.delete()
        if not self.channel_is_valid(ctx.channel):
            return

        session: BaseSession = self.get_session(ctx.guild)
        if not isinstance(session, BackgroundSession):
            return
        print("DEBUG: -> command resume")
        vc = session.voice_client
        if vc and vc.is_paused():
            vc.resume()

    @commands.command()
    async def context(self, ctx: Context, context_name: str, phase_name: Optional[str]):
        session: Optional[BaseSession] = self.get_session(ctx.guild)
        print(f"DEBUG: -> command context {context_name} {phase_name}")
        if session is None:
            # Connect
            context: Optional[PhasedContext] = self.ctx_groups.get(context_name, None)
            if context is None:
                return await ctx.channel.send(f"No such context {context_name}!")

            if ctx.author.voice is None:
                return await ctx.channel.send("User not in voice channel!")

            session = await self.new_context(ctx, context_name)
        else:
            if not isinstance(session, BackgroundSession):
                return
            if context_name not in self.ctx_groups:
                return await session.send_message(f"No such context {context_name}!")

            session.set_context(context_name, deepcopy(self.ctx_groups[context_name]))

        if phase_name is None:
            return session.play_default()

        if phase_name not in session.context.playlists:
            return await session.send_message(f"No phase {phase_name} in context {session.context_name}!")

        session.play_list(phase_name)

    @commands.command()
    async def phase(self, ctx: Context, phase_name: str):
        if not self.channel_is_valid(ctx.channel):
            return

        session: BaseSession = self.get_session(ctx.guild)
        if not isinstance(session, BackgroundSession):
            return
        print(f"DEBUG: -> command phase {phase_name}")
        if phase_name not in session.context.playlists:
            print(f"No phase {phase_name} in context {session.context_name}!")
            return await session.send_message(f"No phase {phase_name} in context {session.context_name}!")

        session.play_list(phase_name)

    @commands.command(name="list")
    async def list_items(self, ctx: Context, what: str):
        if not self.channel_is_valid(ctx.channel):
            return

        session: BaseSession = self.get_session(ctx.guild)
        if not isinstance(session, BackgroundSession):
            return
        print(f"DEBUG: -> command list {what}")
        if what == "contexts":
            return await session.send_message(str(list(self.ctx_groups.keys())))

        if self.channel_is_valid(ctx.channel) and what == "phases":
            return await session.send_message(str(list(self.get_session(ctx.guild).context.playlists.keys())))

        return await session.send_message("Valid options are [\"contexts\", \"phases\"]")

    @commands.command()
    async def skip(self, ctx: Context):
        if not self.channel_is_valid(ctx.channel):
            return

        session: BaseSession = self.get_session(ctx.guild)
        if not isinstance(session, BackgroundSession):
            return

        print("DEBUG: -> command skip")
        session.next_track()

    @commands.command()
    async def shutdown(self, ctx: Context):
        print("DEBUG: -> command shutdown")
        await ctx.send("shutting down!")
        await ursa_bot.close()


@ursa_bot.event
async def on_ready():
    print(f"Logged in as {ursa_bot.user.name} ({ursa_bot.user.id})")
    print(f"Invite link: {INVITE_LINK}")


#    while True:
#        cmd = input()
#        print(f"Received command: {cmd}")
#        if cmd == "exit":
#            exit(0)


def main() -> int:
    argv = sys.argv[1:]
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument('-c', '--config', default=(Path.home() / ".config" / "ursa.json").as_posix(),
                        type=str, help="config file for Ursa", dest='config')
    # parser.add_argument('-g', '--gui', action="store_true", default=False, help="Use pyqt gui method")

    ns: Namespace = parser.parse_args(argv)

    try:
        config: Dict = load(open(ns.config, 'r'))
    except FileNotFoundError:
        config: Dict = dict()

    assert isinstance(config, dict)
    logging.basicConfig(level=logging.INFO)

    # if ns.gui:
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    gui = MainWindow()
    gui.tracks_dock.load_model(config)
    gui.show()
    loop.run_forever()
    # else:
    #     ursa_bot.add_cog(Ursa(ursa_bot, config))
    #     ursa_bot.run(settings.TOKEN)

    return 0


if __name__ == "__main__":
    sys.exit(main())
