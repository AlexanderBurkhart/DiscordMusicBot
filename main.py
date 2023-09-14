import discord
from discord.ext import commands, tasks
import youtube_dl
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('discord_token')

activity = discord.Activity(type=discord.ActivityType.custom, name='f', state='Play music with /play')
bot = commands.Bot(command_prefix='//', activity=activity)

queue = []
stopped = False

# Define a function to play audio in a voice channel
async def play_audio(ctx, link):
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        queue[0]['title'] = info.get('title', None)
        url2 = info['formats'][0]['url']
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(url2))

# Define a command to add a YouTube link to the queue
@bot.slash_command(name='play', description='Play audio from a YouTube link', guild_ids=['385298091332468736', '233955926518923265'])
async def play(ctx: commands.Context, link: str):
    global queue
    global stopped
    stopped = False
    if not link:
        return
    await ctx.respond(f'Adding audio to the queue...')
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    ydl_opts = {
        'format': 'worstaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '1',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        title = info.get('title', None)
    queue.append({
        'title': title,
        'ctx': ctx, 
        'link': link, 
        'has_played': False
    })
    await ctx.send(f'Added {link} to the queue.')

@bot.slash_command(name='resume', description='Play audio from a YouTube link', guild_ids=['385298091332468736', '233955926518923265'])
async def resume(ctx: commands.Context):
    global stopped
    stopped = False
    if queue:
        await ctx.respond('***Resumed*** ▶️')
    else:
        await ctx.respond('***Nothing to resume...***')

# Define a command to stop audio playback
@bot.slash_command(name='stop', description='Stop audio playback', guild_ids=['385298091332468736', '233955926518923265'])
async def stop(ctx: commands.Context):
    await stop_audio(ctx)
    await ctx.respond('***Stopped*** 🛑')

@bot.slash_command(name='skip', description='Skip audio playback', guild_ids=['385298091332468736', '233955926518923265'])
async def skip(ctx: commands.Context):
    await stop(ctx)
    await play(ctx, '')
    await ctx.respond('***Skipped*** ⏭️')

@bot.slash_command(name='clear', description='Clear queue', guild_ids=['385298091332468736', '233955926518923265'])
async def clear(ctx: commands.Context):
    global queue
    queue = []
    await ctx.respond('***Cleared queue*** 💥')

@bot.slash_command(name='current', description='Get current playback', guild_ids=['385298091332468736', '233955926518923265'])
async def current(ctx: commands.Context):
    global queue
    title = queue[0]['title']
    link = queue[0]['link']
    await ctx.respond('## *Currently Playing 💿*\n [%s](%s)' % (title, link))
        


# Define a command to stop audio playback
@bot.slash_command(name='queue', description='View audio queue', guild_ids=['385298091332468736', '233955926518923265'])
async def view_queue(ctx: commands.Context):
    styled_queue_string = '## Current Queue\n'
    for i, clip in enumerate(queue):
        styled_queue_string += '`%i.` [%s](%s) %s\n' % (i+1, clip['title'], clip['link'], '[***Current***]' if i == 0 else '')
    await ctx.respond(styled_queue_string)

# Define a function to stop audio playback
async def stop_audio(ctx):
    global stopped
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        stopped = True
        ctx.voice_client.stop()

# Define a background task to play the next item in the queue automatically
@tasks.loop(seconds=4)
async def background_task():
    global stopped, queue
    if stopped or not queue:
        return 

    clip_data = queue[0]
    ctx = clip_data['ctx']
    link = clip_data['link']
    has_played = clip_data['has_played']

    if ctx.voice_client and not ctx.voice_client.is_playing():
        if has_played:
            queue.pop(0)
            if queue:
                clip_data = queue[0]
                ctx = clip_data['ctx']
                link = clip_data['link']
                has_played = clip_data['has_played']
                queue[0]['has_played'] = True
                await play_audio(ctx, link)
            else:
                stopped = False
        else:
            queue[0]['has_played'] = True
            await play_audio(ctx, link)
            

# Start the background task
background_task.start()

if __name__ == '__main__':
    print('Running')
    bot.run(DISCORD_TOKEN)