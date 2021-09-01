import asyncio
from typing import Optional
import discord
import difflib
from discord import Message
from os import getenv
from dotenv import load_dotenv
from itertools import chain

from random import choice, random
from storage import UserData, compute_quote_distribution, get_all_quotes, read_users, write_users

# TODO: Add a feature that reduces immediate repetitions of quotes.

COMMAND_CHARACTER = '!'
MAX_QUOTE_LENGTH = 1500
QUOTEPATH = "quotes/"

def generate_quote_path(name: str) -> str:
    return f"{QUOTEPATH}{name}quotes.txt"

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
    if head in ("rmquote", "removequote"):
        await rmquote(msg, tail)
    if head == "quotestats":
        await quotestats(msg, tail)
    if head == "ballsdeep":
        await ballsdeep(msg)
    if head == "joinme":
        await joinme(msg, tail)
    if head == "ag":
        await ag(msg, tail)

async def pieces(msg: Message):
    """
    Usage:
    !pieces
    sends three random pieces.
    """
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    content = ", ".join([choice(pieces) for _ in range(3)])
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


async def quote(msg: Message, tail) -> bool:
    """
    Usage:
    !quote [name (optional)] [num (optional)]
    Sends a random quote from a random user. If num is specified,
    it will send [num] random quotes from the specified user.
    Returns a boolean to indicate success or failiure.
    """

    if len(tail) == 2:
        name, num, *_ = tail
        num = int(num)
        if num > 5:
            await send(msg, "You may only request up to five sequential quotes.")
            return False
        for _ in range(num):
            result = await quote(msg, [name])
            if not result:
                return False
        return True

    if len(tail) == 0:
        name = weighted_choice(user_quote_distribution)
    else:
        name, *_ = tail

        name = await handle_name(msg, name)
        if name == None: return False

    filename = generate_quote_path(name)
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    await send(msg, f"{name}: \"{choice(qs)}\"")
    return True

async def handle_name(msg, name: "Optional[str]") -> "Optional[str]":
    """
    Converts a user-entered name into a name that can be used for quote lookup.
    """

    if name == "me":
        name = user_find(msg.author.name, msg.author.discriminator)
    if name == "anyone":
        name = weighted_choice(user_quote_distribution)

    if name not in lads:
        await send(msg, f"\"{name}\" is not in my list of users. Use !joinme {name} if you are {name} and want to be added.")
        return None
    elif name == None:
        await send(msg, "I don't know who you are. Use !joinme [name] if you want to be added.")
        return None

    return name


def user_find(username, discriminator):
    """
    Finds a user by name and discriminator. (user#0000)
    """

    for u in userset:
        if u.username == username and u.code == discriminator:
            return u.name
    return None


def character_distance(a: str, b: str) -> int:
    """
    Returns the number of changes that must be made to convert
    string a to string b.
    """
    count = 0
    for x in difflib.Differ().compare(f"{a}\n", f"{b}\n"):
        if x[0] == ' ': continue
        count += 1
    return count

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
    filename = generate_quote_path(name)
    with open(filename, 'r') as f:
        qs = (strip_endline(q) for q in f)
        diffs = (character_distance(quote.lower(), q.lower()) for q in qs)
        preds = (d <= 2 for d in diffs)
        if any(preds):
            await send(msg, f"Not adding quote: is already in the list of quotes for {name}.")
            return

    if "@" in quote:
        await send(msg, "Not adding quote: Quote contains an '@' character, which is not allowed.")
        return

    if len(quote) > MAX_QUOTE_LENGTH:
        await send(msg, f"Not adding quote: Quote is too long. Maximum is {MAX_QUOTE_LENGTH} characters.")
        return

    with open(filename, 'a') as f:
        f.write("\n")
        f.write(quote)
    await send(msg, f"added quote \"{quote}\" to file {filename}")

async def rmquote(msg, tail):
    """
    Usage:
    !rmquote [name] [quote]
    Removes the quote most similar to the one specified.
    """
    if len(tail) < 2:
        await send(msg, "You have to specify a name and a quote (of at least one word) to remove.")
        return

    name, *quotelist = tail

    name = await handle_name(msg, name)
    if name == None: return

    quote = " ".join(quotelist)
    filename = generate_quote_path(name)
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    diffs = {q: character_distance(quote.lower(), q.lower()) for q in qs}
    closest = min(diffs, key=lambda x: diffs[x])
    if diffs[closest] == 0:
        await send(msg, f"Removing quote.")
    else: 
        await send(msg, f"Closest match found: \"{closest[:1000]}\"")
        await send(msg, "Remove this quote? (y/n)")
        do_remove = await get_yes_no(msg)
        if not do_remove:
            await send(msg, "Not removing quote.")
            return

    with open(filename, 'r') as f:
        lines = [strip_endline(q) for q in f]
    with open(filename, 'w') as f:
        for line in filter(lambda q: q != closest, lines):
            f.write(f"{line}\n")

    # check the file has actually had the quote removed
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
        assert closest not in qs

    await send(msg, f"removed quote \"{closest[:1000]}\" from file {filename}")

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

    filename = generate_quote_path(name)
    with open(filename, 'r') as f:
        qs = [strip_endline(q) for q in f]
    count = len(qs)
    avglen = int(sum(map(len, qs)) / count + 0.5)
    await send(msg, f"{name} has {count} quotes, with an average quote length of {avglen}.")

async def ag(msg: Message, tail):
    """
    Usage:
    !ag [quote fragment] [num]
    Searches all quotes for the specified quote fragment and returns the N quotes with the highest similarity.
    """
    if tail == []:
        await send(msg, "You have to specify a fragment to search for.")
        return

    if len(tail) >= 2:
        fragment, strnum, *_ = tail
        num = int(strnum)
    else:
        fragment, *_ = tail
        num = 1
    
    if num < 1 or num > 10:
        await send(msg, "You have to specify a number greater than 0 and at most 10.")
        return

    allquotes = chain.from_iterable((map(lambda n: (u.name, n), get_all_quotes(u.name))) for u in userset)

    # find all the quotes that contain the fragment
    matches = (q for q in allquotes if fragment.lower() in q[1].lower())

    # sort the matches by similarity
    matches = sorted(matches, key=lambda q: character_distance(fragment.lower(), q[1].lower()))

    # return the top N matches
    matches = matches[:num]

    # format the matches into a string for sending
    matchstr = "\n".join(f"{i+1}. {q[0]}: {q[1].strip()}" for i, q in enumerate(matches))

    if len(matches) == 0:
        await send(msg, "No matches found.")
    else:
        await send(msg, f"Found {len(matches)} matches for \"{fragment}\":\n{matchstr}")

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

async def get_yes_no(message: Message, timeout=10) -> bool:
    """
    Checks if a user responded with either 'y' or 'n'.
    False on timeout.
    """
    def check(msg):
        return msg.content.lower() in ('y', 'n')
    
    try:
        result = await client.wait_for('message', check=check, timeout=timeout)
        return result.content.lower() == 'y'
    except asyncio.TimeoutError:
        await send(message, "Answer timed out.")
        return False


if __name__ == "__main__":
    client.run(token)
