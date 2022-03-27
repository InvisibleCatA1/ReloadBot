# Create a simple discord bot in python
import asyncio
import math
import os
import random
import re
from datetime import datetime

import asyncpraw
import discord
import dotenv
import requests
import youtube_dl
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

dotenv.load_dotenv()

client = commands.Bot(command_prefix='>', help_command=None, intents=intents)

# using praw.ini for reddit credentials
reddit = asyncpraw.Reddit("bot1", user_agent="bot1 discord memes")

TOKEN = os.getenv("TOKEN")
hypixelKey = os.getenv("KEY")


async def youtube_search(query):
    url = "https://www.youtube.com/results?search_query=" + query
    html = requests.get(url).text
    video_id = re.search(r'/watch\?v=(.{11})', html).group(1)
    return "https://www.youtube.com/watch?v=" + video_id


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name='>help'))
    # print basic info about the bot and the reddit account
    print(f'Logged in as [{client.user.name}] for discord bot')
    print(f'User ID: [{client.user.id}]')
    print('------')
    print(f'Logged in as [{await reddit.user.me()}] for Reddit account')
    print('------')
    # print the name of all guilds the bot is in
    print(f'Bot is in {len(client.guilds)} guilds:')
    for guild in client.guilds:
        print(f' - {guild.name}')
    print('------')
    print("Hypixel API key: " + hypixelKey)
    print('------')


@client.event
async def on_memeber_join(member):
    await member.create_dm();
    await member.dm_channel.send("Hi {0}, welcome to the server! jk fuck u".format(member.name))


@client.command()
async def ping(ctx):
    await ctx.reply(f'Pong! {round(client.latency * 1000)}ms')


# create a meme command that sends a random meme from reddit
@client.command()
async def meme(ctx):
    subreddit = await reddit.subreddit('dankmemes')
    post = await subreddit.random()
    await ctx.reply(post.url)


@client.command()
async def insult(ctx, member: discord.Member):
    await ctx.reply(
        f'{member.mention} you are a {random.choice(["idiot", "bozo", "idk im to lazy to think of a insult"])}')


# create a command that says the length of someone's pp
@client.command()
async def pp(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    length = (len(member.display_name + member.discriminator + member.top_role.name) * member.top_role.position) / 50
    res = "8".ljust(int(length * 1.5) + len("8"), "=")
    await ctx.reply(f'{member.mention} pp: {res}D')


# gets youtube video from a search without a link
@client.command()
async def youtube(ctx, *, query):
    await ctx.reply(f"{youtube_search(query)} Video found")


# create a command that says your Hypiexl level
@client.command()
async def hypixel(ctx, name: str):
    await ctx.send("Getting Hypixel info...")
    data = requests.get(
        url="https://api.hypixel.net/player",
        params={
            "key": hypixelKey,
            "name": name
        }
    ).json()

    if data['success']:
        player = data['player']
        if player is None:
            print("Player not found")
            await ctx.send("Error: **Player not found**")
            return

        network_level = (math.sqrt((2 * player["networkExp"]) + 30625) / 50) - 2.5
        network_level = round(network_level, 2)
        # create a variable for the players last login formated as a date
        last_login = datetime.fromtimestamp(player["lastLogin"] / 1000)

        rank = player['newPackageRank'] if player['newPackageRank'] else None
        if rank == "VIP":
            rank = "Vip"
        elif rank == "VIP_PLUS":
            rank = "Vip+"
        elif rank == "MVP":
            rank = "Mvp"
        elif rank == "MVP_PLUS":
            rank = "Mvp+"
        elif rank == "MVP_PLUS_PLUS":
            rank = "Mvp++"
        else:
            rank = "Default"

        # send the info
        embed = discord.Embed(title="Hypixel info", description=f"Here is {name}'s Hypixel stats", color=0x00ff00)
        embed.add_field(name="Rank", value=rank, inline=True)
        embed.add_field(name="Network Level", value=str(network_level), inline=True)
        # add a field for there last login but format it as a date
        embed.add_field(name="Last Login", value=str(last_login), inline=True)
        await ctx.send(embed=embed)

    if not data['success']:
        await ctx.send("Error: **" + data['cause'] + "**")


# create a command that searches for a song on YouTube and plays it in a voice channel that the author is in
@client.command()
async def play(ctx, *, query):
    # get the video for the query
    await ctx.send("Getting video for song...")
    video = await youtube_search(query)
    await ctx.send(f"found video {video}")

    isSongThere = os.path.isfile("song.mp3")
    try:
        if isSongThere:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("Please wait until the current song finishes or stop it")
        return
    await ctx.send("Joining voice channel...")

    channel = ctx.author.voice.channel

    voice = await channel.connect()

    if voice and voice.is_connected():
        await voice.disconnect()
        voice = await channel.connect()

    await ctx.send(f"Joined voice channel: {channel}")

    youtube_dl_options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(youtube_dl_options) as ydl:
        await ctx.send("Downloading audio...")
        ydl.download([video])
    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            os.rename(file, 'song.mp3')

    await ctx.send("Playing song...")
    voice.play(discord.FFmpegPCMAudio(source="song.mp3", executable="C:/Program Files/FFmPEG/bin/ffmpeg.exe"))


# create a command that pauses the song
@client.command()
async def pause(ctx):
    voice = ctx.author.voice.channel
    voice.pause()
    await ctx.send("Paused song")


# create a command that resumes the song
@client.command()
async def resume(ctx):
    voice = ctx.author.voice.channel
    voice.resume()
    await ctx.send("Resumed song")


# make that stop the song
@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("Stopped song")
    else:
        await ctx.send("No song playing")


# make that disconnect from the voice channel
@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send("Disconnected from voice channel")
    else:
        await ctx.send("Not connected to voice channel")


# make a command that starts a number guessing game
# the game will have a random number between 1 and 100
# the user will have to guess the number
# if the user guesses the number correctly, they will get a message saying they won
# if the user guesses the number incorrectly, they will get a message saying if they guessed higher or lower
# if the user guesses the number correctly in 5 tries, they will get a message saying they won the game
# if the user guesses the number incorrectly in 5 tries, they will get a message saying they lost the game
@client.command()
async def guess(ctx):
    await ctx.send("Guess a number between 1 and 100")
    number = random.randint(1, 100)
    tries = 0
    while tries < 10:
        UserGuess = await client.wait_for('message')
        guessNumber = int(UserGuess.content)
        if guessNumber == number:
            await ctx.send("**You won!**")
            # add a check reaction to the message
            await UserGuess.add_reaction("✅")
            break
        elif guessNumber > number:
            await ctx.send("You guessed to high")
        elif guessNumber < number:
            await ctx.send("You guessed to low")
        tries += 1
    if tries == 10:
        await ctx.send(f"**You lost!** The number was {number}")


# create a command that allows user to create a suggestion for a project
# the bot will send a message to the channel call "suggestions"
# the bot will delete the message that the user sent after the bot has sent a message to the channel
# the suggestion will be in a embed message with a check reaction and a X reaction
@client.command()
async def suggest(ctx, *, suggestion):
    await ctx.message.delete()

    embed = discord.Embed(title="Suggestion", description=suggestion, color=0x00ff00)
    embed.set_footer(text="Suggested by " + ctx.author.name)
    embed.set_thumbnail(url=client.u)
    embed.timestamp = datetime.utcnow()
    channel = client.get_channel(957674791828090920)
    message = await channel.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")

# create a serverinfo command that will show the server name, the number of members, the number of channels,
# and the number of roles
@client.command()
async def serverinfo(ctx):
    embed = discord.Embed(title=ctx.guild.name, description=f"Here is the server info for {ctx.guild.name}",
                          color=0x00ff00)
    embed.add_field(name="Members", value=ctx.guild.member_count)
    embed.add_field(name="Channels", value=str(len(ctx.guild.channels)))
    embed.add_field(name="Roles", value=str(len(ctx.guild.roles)))
    await ctx.send(embed=embed)


# create a command the displays all the commands as a help command
# the prefix is >
@client.command()
async def help(ctx):
    embed = discord.Embed(title="Help", description="Here are all of the commands", color=0x00ff00)
    embed.add_field(name=">play", value="Plays a song from youtube", inline=False)
    embed.add_field(name=">pause", value="Pauses the song", inline=False)
    embed.add_field(name=">resume", value="Resumes the song", inline=False)
    embed.add_field(name=">stop", value="Stops the song", inline=False)
    embed.add_field(name=">leave", value="Leaves the voice channel", inline=False)
    embed.add_field(name=">guess", value="Guess a number between 1 and 100", inline=False)
    embed.add_field(name=">suggest", value="Suggest a change for Reload", inline=False)
    embed.add_field(name=">help", value="Displays all of the commands", inline=False)
    embed.add_field(name=">ping", value="Displays the bot's ping", inline=False)
    embed.add_field(name=">hypixel", value="Displays the hypixel stats of the user", inline=False)
    embed.add_field(name=">serverinfo", value="Displays the server info", inline=False)
    embed.add_field(name=">pp", value="Displays the pp length of a user", inline=False)

    await ctx.send(embed=embed)


# handle unknown commands
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("That command does not exist")
    else:
        print(error)


client.run(TOKEN)
