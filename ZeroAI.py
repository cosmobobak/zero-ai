import discord
from discord import Message
from os import getenv
from dotenv import load_dotenv

from random import choice, random
from storage import UserData, read_users, save_user, write_users

COMMAND_CHARACTER = '!'

lads = {"finegold", "gotham", "jamie", "kit", "mike", "cosmo",
        "edward", "marina", "tegan", "elyn", "roman", "adam", 
        "cameron", "kim"}

userset = read_users()

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
async def on_message(msg: Message):
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
    if head == "quotestats":
        await quotestats(msg, tail)
    if head == "ballsdeep":
        await ballsdeep(msg)
    if head == "joinme":
        await associate_user_with_id(msg, tail)

async def pieces(msg: Message):
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    content = ", ".join([choice(pieces) for i in range(3)])
    await send(msg, content)

async def associate_user_with_id(msg: Message, tail):
    if not len(tail) >= 1:
        await send(msg, "You have to specify a name for !joinme to work.")
        return
    name, *_ = tail
    
    ud = UserData(name, msg.author.name, msg.author.discriminator)
    userset.discard(ud)
    userset.add(ud)

    await send(msg, f"Saving {name}'s associated account as {msg.author.name}#{msg.author.discriminator}")

    write_users(userset)

async def quote(msg: Message, tail):
    assert len(tail) >= 1
    name, *_ = tail

    name = await handle_name(msg, name)
    if name == None: return

    filename = name + "quotes.txt"
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    await send(msg, f"{name}: \"{choice(qs)}\"")

async def handle_name(msg, name):
    if name == "me":
        name = user_find(msg.author.name, msg.author.discriminator)

    if name == None or name not in lads:
        if name != None:
            await send(msg, f"\"{name}\" is not in my list of users. Use !joinme {name} if you are {name} and want to be added.")
        else:
            await send(msg, "I don't know who you are. Use !joinme [name] if you want to be added.")
        return
    return name


def user_find(username, discriminator):
    for u in userset:
        if u.username == username and u.code == discriminator:
            return u.name
    return None

async def addquote(msg: Message, tail):
    assert len(tail) >= 2
    name, *quotelist = tail

    name = await handle_name(msg, name)
    if name == None: return

    quote = " ".join(quotelist)
    filename = name + "quotes.txt"
    with open(filename, 'a') as f:
        f.write("\n")
        f.write(quote)
    await send(msg, f"added quote \"{quote}\" to file {filename}")

async def quotestats(msg: Message, tail):
    assert len(tail) >= 1
    name, *_ = tail

    name = await handle_name(msg, name)
    if name == None: return

    filename = name + "quotes.txt"
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    count = len(qs)
    avglen = int(sum(map(len, qs)) / count + 0.5)
    await send(msg, f"{name} has {count} quotes, with an average quote length of {avglen}.")

async def ballsdeep(msg: Message):
    await send(msg, "[SUCCESSFULLY HACKED FBI - BLOWING UP COMPUTER]")
    for i in range(5, 0, -1):
        await send(msg, f"{i}")

async def send(message: Message, text):
    await message.channel.send(text)

def choose_three_pieces():
    return ", ".join([choice(["pawn", "knight", "bishop", "rook", "queen", "king"]) for _ in range(3)])

if __name__ == "__main__":
    client.run(token)
