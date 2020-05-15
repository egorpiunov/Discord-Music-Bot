import discord
import os
import youtube_dl
from discord.utils import get
from discord.ext import commands
from asyncio import run_coroutine_threadsafe

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._songlist = []
        self._unknown_files = 0
        self._music_path = './music/'
        if os.path.exists(self._music_path):
            self._songlist, self._unknown_files = update_songlist(self._music_path)
        else:
            os.mkdir(self._music_path)

    async def boxed_print(self, ctx, text):
        await ctx.message.channel.send('```' + text + '```')

    @commands.command(name = 'list', brief = 'Shows songs list')
    async def list_(self, ctx):
        if not self._songlist:
            await self.boxed_print(ctx, 'No songs! Use "bro download" to download songs')
            return
        i = 0
        string = ''
        for name in self._songlist:
            i += 1
            string += f'{i!s}. {name[:-5]!s}\n'
        await self.boxed_print(ctx, string)
        if self._unknown_files == 1:
            await self.boxed_print(ctx, 'Also there is a file with unknown extension. Check your music folder.')
        elif self._unknown_files > 1:
            await self.boxed_print(ctx, f'Also there are {self._unknown_files!s} files with unknown extension. Check your music folder.')

    @commands.command(brief = 'Stops playing audio')
    async def stop(self, ctx, loop = ''):
        if loop == 'loop':
            self._stop_loop = True
        elif ctx.voice_client.is_connected():
            await ctx.message.guild.voice_client.disconnect()

    @commands.command(brief = 'Plays song from list')
    async def play(self, ctx, number, loop = ''):
        status = get(self.client.voice_clients, guild=ctx.guild)
        try:
            if not status and ctx.message.author.voice != None:
                await ctx.message.author.voice.channel.connect()
        except:
            await self.boxed_print(ctx, 'Connect to a voice channel before playing')
        name = self._songlist[int(number) - 1]
        song = self._music_path + self._songlist[int(number) - 1]
        await self.boxed_print(ctx, 'Playing: ' + name[:-5])
        self._stop_loop = False
        def after_play(error):
            if loop == 'loop' and not self._stop_loop:
                try:
                    ctx.message.guild.voice_client.play(discord.FFmpegOpusAudio(song), after = after_play)
                except:
                    pass
            else:
                coroutine = ctx.voice_client.disconnect()
                future = run_coroutine_threadsafe(coroutine, self.client.loop)
                try:
                    future.result()
                except:
                    print('Disconnect has failed. Run "stop" manually', error)
        ctx.message.guild.voice_client.play(discord.FFmpegOpusAudio(song), after = after_play)

    @commands.command(brief = 'Downloads audio from YouTube')
    async def download(self, ctx, url):
        ydl_opts = {
            'format': 'bestaudio/opus',
            'outtmpl': '/music/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            await self.boxed_print(ctx, 'Song downloaded: \n' + info['title'])
        self._songlist, self._unknown_files = update_songlist(self._music_path)
        await self.list_(ctx)

    @commands.command(brief = 'Removes a song selected from the list')
    async def remove(self, ctx, number = 0):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            if (1 <= int(number) <= len(self._songlist)):
                song = self._songlist.pop(int(number) - 1)
                os.remove(self._music_path + song)
                await self.boxed_print(ctx, f'Song {song[:-5]} has been deleted')
            else:
                await self.boxed_print(ctx, f'Select an existing song from the list')

    @commands.command(brief = 'Flushes the music directory')
    async def flush(self, ctx):
        status = get(self.client.voice_clients, guild=ctx.guild)
        if not status:
            for filename in os.scandir(self._music_path):
                os.remove(filename.path)
            await self.boxed_print(ctx, 'Music folder is now empty')
        self._songlist.clear()

def update_songlist(music_path, ext = '.opus'):
    songlist = []
    unknown_files = 0
    for filename in os.listdir(music_path):
        if filename.endswith(ext):
            songlist.append(filename)
        else:
            unknown_files += 1
    return songlist, unknown_files

def setup(client):
    client.add_cog(Music(client))
