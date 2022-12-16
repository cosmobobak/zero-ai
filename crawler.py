import discord
from tqdm.asyncio import tqdm
from discord.ext import commands
from os import getenv
from dotenv import load_dotenv

load_dotenv()

token = getenv('TOKEN')

bot = commands.Bot('!')

@bot.command()
async def genhist(ctx, member: discord.Member):
    counter = 0
    with open('history.txt', 'w') as f:
        for channel in ctx.guild.channels:
            print(channel.name)
            if type(channel) not in [discord.VoiceChannel, discord.CategoryChannel] and channel.name not in ["arrivals-and-departures", "secret-general", "bot-management", "high-score", "you-just-lost-the-game", "chess-memes"]:
                async for message in tqdm(channel.history(limit = 100000000000)):
                    if message.author == member:
                        counter += 1
                        f.write(f"{message.created_at} {message.content}\n")

if __name__ == "__main__":
    bot.run(token)