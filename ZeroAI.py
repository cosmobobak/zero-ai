import discord
from discord import Message
from os import getenv
from dotenv import load_dotenv

from random import choice, random
from storage import UserData, compute_quote_distribution, read_users, save_user, write_users

COMMAND_CHARACTER = '!'

lads = {"finegold", "gotham", "jamie", "kit", "mike", "cosmo",
        "edward", "marina", "tegan", "elyn", "roman", "adam", 
        "cameron", "kim"}

user_quote_distribution: "dict[str, int]" = compute_quote_distribution()

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

def weighted_choice(distribution_dict: "dict[str, int]") -> str:
    """
    Chooses a random element from a dictionary based on the weights
    of the elements.
    """
    total = sum(distribution_dict.values())
    r = random() * total
    for key, weight in distribution_dict.items():
        r -= weight
        if r <= 0:
            return key
    assert False

def sanitise_message(message_string: str) -> "tuple[str, list[str]]":
    """
    Takes a string representing a discord message and returns a tuple of 
    (the lead character, a list of the words in the rest of the message)
    """
    if len(message_string) in [0, 1]:
        return '', []
    head, *tail = message_string
    return head, "".join(tail).split(" ")


def strip_endline(s):
    return s if s[-1] != '\n' else s[:-1]

async def map_uid_to_handle(uid: str):
    user = await client.fetch_user(int(uid[3:-1]))
    return user.name + "#" + user.discriminator

@client.event
async def on_message(msg: Message):
    if msg.author == client.user: return

    lead_char, cmd = sanitise_message(msg.content)
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
        await joinme(msg, tail)

async def pieces(msg: Message):
    """
    Usage:
    !pieces
    sends three random pieces.
    """
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    content = ", ".join([choice(pieces) for i in range(3)])
    await send(msg, content)

async def joinme(msg: Message, tail):
    """
    Usage:
    !joinme [name]
    Adds a user to the list of known users.
    """
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
    """
    Usage:
    !quote [name (optional)] [num (optional)]
    Sends a random quote from a random user. If num is specified,
    it will send [num] random quotes from the specified user.
    """

    if len (tail) == 2:
        name, num, *_ = tail
        num = int(num)
        for _ in range(num):
            await quote(msg, [name])
        return

    if len(tail) == 0:
        name = weighted_choice(user_quote_distribution)
    else:
        name, *_ = tail

        name = await handle_name(msg, name)
        if name == None: return

    filename = name + "quotes.txt"
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    await send(msg, f"{name}: \"{choice(qs)}\"")

async def handle_name(msg, name):
    """
    Converts a user-entered name into a name that can be used for quote lookup.
    """

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
    """
    Finds a user by name and discriminator. (user#0000)
    """

    for u in userset:
        if u.username == username and u.code == discriminator:
            return u.name
    return None

async def addquote(msg: Message, tail):
    """
    Usage:
    !addquote [name] quote...
    Adds a quote to the specified user's list of quotes.
    """
    if len(tail) < 2:
        await send(msg, "You have to specify a name and a quote (of at least one word) to add.")
        return
    
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
    """
    Usage:
    !quotestats [name]
    Prints information about the quotes in the specified user's list.
    """

    if len(tail) < 1:
        await send(msg, "You have to specify a name to get quote stats for.")
        return
    
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
    """
    Usage:
    !ballsdeep
    This is a dumb function.
    """
    await send(msg, "[SUCCESSFULLY HACKED FBI - BLOWING UP COMPUTER]")
    for i in range(5, 0, -1):
        await send(msg, f"{i}")

async def send(message: Message, text):
    """
    A simpler send function.
    """
    await message.channel.send(text)

if __name__ == "__main__":
    client.run(token)
