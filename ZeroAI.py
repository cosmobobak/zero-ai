import discord
from os import getenv
from dotenv import load_dotenv

from random import choice, random
from storage import read_users, save_user

COMMAND_CHARACTER = '!'

lads = {"finegold", "gotham", "jamie", "kit", "mike", "cosmo",
        "edward", "marina", "tegan", "elyn", "roman", "adam"}

usermap = read_users()

HELP_TEXT = """My commands are:
play [ttt, tictactoe, tic-tac-toe, noughts-and-crosses]
play [chess]."""

load_dotenv()

token = getenv('TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


def process(s: str) -> "tuple[str, list[str]]":
    if len(s) == 0 or len(s) == 1:
        return '', []
    head = s[0]
    tail = s[1:]
    return head, tail.split()


def strip_endline(s):
    return s if s[-1] != '\n' else s[:-1]

async def map_uid_to_handle(uid: str):
    user = await client.fetch_user(int(uid[3:-1]))
    return user.name + "#" + user.discriminator

@client.event
async def on_message(msg):
    if msg.author == client.user: return

    lead_char, cmd = process(msg.content)
    if lead_char != COMMAND_CHARACTER: return
    if len(cmd) == 0: return

    print(cmd)

    head, *tail = cmd

    if head == "pieces":
        await pieces(msg)
    if head == "quote":
        await quote(msg, tail)
    if head == "addquote":
        await addquote(msg, tail)
    if head == "adduser":
        await adduser(msg, tail)
    if head == "quotestats":
        await quotestats(msg, tail)
    if head == "ballsdeep":
        await ballsdeep(msg)

async def pieces(msg):
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    content = ", ".join([choice(pieces) for i in range(3)])
    await send(msg, content)

async def quote(msg, tail):
    assert len(tail) >= 1
    name, *_ = tail
    filename = name + "quotes.txt"
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    await send(msg, f"{name}: \"{choice(qs)}\"")

async def addquote(msg, tail):
    assert len(tail) >= 2
    name, *quotelist = tail

    assert name in lads or name == "me"

    if name == "me":
        name = usermap.get(msg.author, default="NO_PERSON")
    if name == "NO_PERSON" or name not in lads: return
    quote = " ".join(quotelist)
    filename = name + "quotes.txt"
    with open(filename, 'a') as f:
        f.write("\n")
        f.write(quote)
    await send(msg, f"added quote \"{quote}\" to file {filename}")

async def adduser(msg, tail):
    assert len(tail) == 2
    name, uid = tail
    if uid == "me": 
        save_user(msg.author, name)
    else: 
        handle = await map_uid_to_handle(uid)
        save_user(handle, name)

async def quotestats(msg, tail):
    assert len(tail) >= 1
    name, *_ = tail
    filename = name + "quotes.txt"
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    count = len(qs)
    avglen = int(sum(map(len, qs)) / count + 0.5)
    await send(msg, f"{name} has {count} quotes, with an average quote length of {avglen}.")

async def ballsdeep(msg):
    await send(msg, "[SUCCESSFULLY HACKED FBI - BLOWING UP COMPUTER]")
    for i in range(5, 0, -1):
        await send(msg, f"{i}")

async def send(message, text):
    await message.channel.send(text)

def choose_three_pieces():
    return ", ".join([choice(["pawn", "knight", "bishop", "rook", "queen", "king"]) for _ in range(3)])

if __name__ == "__main__":
    client.run(token)
