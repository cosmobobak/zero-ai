import asyncio
from collections import defaultdict
import os
import subprocess
from textproc import character_distance, strip_endline
import typing
#async scheduler so it does not block other events
#from apscheduler.schedulers.asyncio import AsyncIOScheduler
#from apscheduler.triggers.cron import CronTrigger
from markovify.text import NewlineText
from markov import generate_quote, regenerate_models
from typing import Any, Optional
import discord
import difflib
import markovify
from discord import Message
from os import getenv
from dotenv import load_dotenv
from itertools import chain

from random import choice, sample, random
from storage import UserData, compute_quote_distribution, file_contains_quote, get_all_quotes, is_known_user, read_users, touch, write_users

# TODO: Add a feature that reduces immediate repetitions of quotes.

CMDCHAR = '!'
MAX_QUOTE_LENGTH = 1500
MAX_QUOTE_SEARCH_RESULTS = 50
QUOTEPATH = "quotes/"

REFRESH_MODEL_THRESHOLD = 30
markov_models: "dict[str, NewlineText]" = dict()
time_since_model_refresh: int = 0

hindsight = 1

manuals: "dict[str, str]" = {}
aliases: "dict[str, list[str]]" = defaultdict(list)

def generate_quote_path(name: str) -> str:
    return f"{QUOTEPATH}{name}quotes.txt"

ANSWERS = ["It is Certain.",
           "It is decidedly so.",
           "Without a doubt.",
           "Yes definitely.",
           "You may rely on it.",

           "As I see it, yes.",
           "Most likely.",
           "Outlook good.",
           "Yes.",
           "Signs point to yes.",

           "Reply hazy, try again.",
           "Ask again later.",
           "Better not tell you now.",
           "Cannot predict now.",
           "Concentrate and ask again.",

           "Don't count on it.",
           "My reply is no.",
           "My sources say no.",
           "Outlook not so good.",
           "Very doubtful.",
           ]

user_quote_distribution: "dict[str, int]" = compute_quote_distribution()

userset = read_users()

def usernames_as_strs(uset: "set[UserData]") -> "list[str]":
    return [u.name for u in uset]

load_dotenv()

token = getenv('TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

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



async def map_uid_to_handle(uid: str):
    user = await client.fetch_user(int(uid[3:-1]))
    return user.name + "#" + user.discriminator

# TODO: use unpacking to make this prettier

@client.event
async def on_message(msg: Message):
    if msg.author == client.user: return

    lead_char, cmd = sanitise_message(msg.content)
    if lead_char != CMDCHAR: return
    if len(cmd) == 0: return

    print(cmd)

    head, *tail = cmd

    if head == "pieces" or head in aliases["pieces"]:
        await pieces(msg)
    if head == "quote" or head in aliases["quote"]:
        await quote(msg, tail)
    if head == "addquote" or head in aliases["addquote"]:
        await addquote(msg, tail)
    if head == "removequote" or head in aliases["removequote"]:
        await removequote(msg, tail)
    if head == "quotestats" or head in aliases["quotestats"]:
        await quotestats(msg, tail)
    if head == "ballsdeep" or head in aliases["ballsdeep"]:
        await ballsdeep(msg)
    if head == "joinme" or head in aliases["joinme"]:
        await joinme(msg, tail)
    if head == "quotesearch" or head in aliases["quotesearch"]:
        await quotesearch(msg, tail)
    if head == "genquote" or head in aliases["genquote"]:
        await genquote(msg, tail)
    if head == "sethindsight" or head in aliases["sethindsight"]:
        await sethindsight(msg, tail)
    if head == "eightball" or head in aliases["eightball"]:
        await eightball(msg, tail)
    if head == "manual" or head in aliases["manual"]:
        await manual(msg, tail)
    if head == "commands" or head in aliases["commands"]:
        await commands(msg)
    if head == "users" or head in aliases["users"]:
        await users(msg, tail)
    if head == "congratulate" or head in aliases["congratulate"]:
        await congratulate(msg, tail)
    if head == "adduser" or head in aliases["adduser"]:
        await adduser(msg, tail)
    if head == "cock" or head in aliases["cock"]:
        await cock(msg)
    if head == "wednesday" or head in aliases["wednesday"]:
        await wednesday(msg)
    if head == "bash" or head in aliases["bash"]:
        await bash(msg, tail)

manuals["pieces"] = f"""
Usage:
{CMDCHAR}pieces
chooses three random chess pieces.
intended to be used to play a chess variant.
"""
async def pieces(msg: Message):
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    a, b, c = sample(pieces, 3)
    await send(msg, f"pieces: {a}, {b}, {c}")

manuals["joinme"] = f"""
Usage:
{CMDCHAR}joinme [name]
Adds a user to the list of known users.
"""
async def joinme(msg, tail):
    if not len(tail) >= 1:
        await send(msg, f"You have to specify a name for {CMDCHAR}joinme to work.")
        return
    name, *_ = tail
    name = name.lower()

    if not any(u.name == name for u in userset):
        await send(msg, f"{name} is not a known user.")
        return

    ud = UserData(name, msg.author.name, msg.author.discriminator, no_associated_account=False)
    # clean out from users by the hash value
    userset.discard(ud)
    # add the new user info
    userset.add(ud)

    await send(msg, f"Saving {name}'s associated account as {msg.author.name}#{msg.author.discriminator}")

    write_users(userset)

manuals["quote"] = f"""
Usage:
{CMDCHAR}quote [name (optional)] [num (optional)]
Sends a random quote from a user. If num is specified,
it will send [num] random quotes from the specified user.
Not specifying user is equivalent to {CMDCHAR}quote anyone.
"""
aliases["quote"].append("q")
async def quote(msg: Message, tail):
    if tail == []:
        name = "anyone"
        n = 1
    elif len(tail) == 1:
        name, *_ = tail
        n = 1
    else:
        name, strn, *_ = tail
        n = int(strn)

    if n > 5:
        await send(msg, "You may only request up to five sequential quotes.")
        return

    name = await handle_name(msg, name) if name not in ("everyone", "anyone") else name
    if name == None: return

    if name not in ("everyone", "anyone"):
        qs = list(map(lambda x: (name, x), get_all_quotes(name)))
    else:
        qs = []
        for u in userset:
            qs += list(map(lambda x: (u.name, x), get_all_quotes(u.name)))
    n = min(n, len(qs))
    if n == 0:
        await send(msg, "No quotes found.")
        return
    choices = sample(qs, n)
    quotes = [f"{n}: \"{strip_endline(q)}\"" for n, q in choices]
    await send(msg, "\n".join(quotes))

async def handle_name(msg: Message, name: "Optional[str]") -> "Optional[str]":
    """
    Converts a user-entered name into a name that can be used for quote lookup.
    """
    if name is not None: 
        name = name.lower()

    if name == "me":
        sender: Any = msg.author
        name = user_find(sender.name, sender.discriminator)
    if name == "anyone":
        name = weighted_choice(user_quote_distribution)

    if name == None:
        await send(msg, f"I don't know who you are. Use {CMDCHAR}adduser [name] if you want to be added.")
        return None

    if not is_known_user(name, userset):
        await send(msg, f"\"{name}\" is not in my list of users. Use {CMDCHAR}adduser {name} if you are {name} and want to be added.")
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

def inc_regen_quotes():
    global time_since_model_refresh
    time_since_model_refresh += 1


manuals["addquote"] = f"""
Usage:
{CMDCHAR}addquote [name] [quote...]
Adds a quote to the specified user's list of quotes.
"""
aliases["addquote"].append("aq")
async def addquote(msg: Message, tail):
    if len(tail) < 2:
        await send(msg, "You have to specify a name and a quote (of at least one word) to add.")
        return
    
    name, *quotelist = tail

    name = await handle_name(msg, name)
    if name == None: return

    quote = " ".join(quotelist)
    filename = generate_quote_path(name)

    touch(filename)

    if "@" in quote:
        await send(msg, "Not adding quote: Quote contains an '@' character, which is not allowed.")
        return

    if '\n' in quote:
        await send(msg, "Not adding quote: Quote contains a newline character, which is not allowed.")
        return

    if file_contains_quote(filename, quote):
        await send(msg, f"Not adding quote: is already in the list of quotes for {name}.")
        return

    if len(quote) > MAX_QUOTE_LENGTH:
        await send(msg, f"Not adding quote: Quote is too long. Maximum is {MAX_QUOTE_LENGTH} characters.")
        return

    with open(filename, 'a') as f:
        f.write("\n")
        f.write(quote)

    inc_regen_quotes()

    await send(msg, f"added quote \"{quote}\" to file {filename}")

manuals["removequote"] = f"""
Usage:
{CMDCHAR}removequote [name] [quote...]
Finds the quote most similar to the one specified, then deletes it if it is an exact match.
If the quote is not an exact match, you will be prompted to confirm deletion.
"""
aliases["removequote"].append("rq")
aliases["removequote"].append("rmquote")
async def removequote(msg, tail):
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
        truncate_width = 200
        await send(msg, f"Closest match found: \"{closest[:truncate_width]}{'...' if len(closest) > truncate_width else ''}\"")
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

manuals["quotestats"] = f"""
Usage:
{CMDCHAR}quotestats [name]
Prints information about the quotes in the specified user's list.
"""
aliases["quotestats"].append("stats")
async def quotestats(msg: Message, tail):
    if len(tail) < 1:
        await send(msg, "You have to specify a name to get quote stats for.")
        return
    
    name, *_ = tail

    def compute_stats(name: str) -> "tuple[int, int]":
        filename = generate_quote_path(name)
        with open(filename, 'r') as f:
            qs = [strip_endline(q) for q in f]
        count = len(qs)
        avglen = int(sum(map(len, qs)) / count + 0.5)
        return count, avglen

    if name == "everyone":
        stats = { u.name: compute_stats(u.name) for u in userset }
        output = "Quote stats for everyone:\n"
        for name, (count, avglen) in sorted(stats.items(), key=lambda r: r[1][0], reverse=True):
            output += f"{name} has {count} quotes, with an average quote length of {avglen}.\n"
        await send(msg, output)
        return

    name = await handle_name(msg, name)
    if name == None: return

    count, avglen = compute_stats(name)
    await send(msg, f"{name} has {count} quotes, with an average quote length of {avglen}.")

manuals["quotesearch"] = f"""
Usage:
{CMDCHAR}quotesearch [quote fragment] [num]
Searches all quotes for the specified quote fragment and returns the N quotes with the highest similarity.
"""
aliases["quotesearch"].append("qsearch")
aliases["quotesearch"].append("qs")
async def quotesearch(msg: Message, tail: "list[str]"):
    if tail == []:
        await send(msg, "You have to specify a fragment to search for.")
        return
    parts = tail
    if len(tail) > 1:
        try:
            n = int(tail[-1])
            parts = tail[:-1]
        except ValueError:
            n = 1
    else:
        n = 1
    if n < 1:
        await send(msg, "You have to specify a number greater than 0.")
        return
    if n > MAX_QUOTE_SEARCH_RESULTS:
        await send(msg, f"You have to specify a number less than or equal to {MAX_QUOTE_SEARCH_RESULTS}.")
        return

    fragment = " ".join(parts)

    # grab all quotes from all files
    allquotes = chain.from_iterable((map(lambda n: (u.name, n), get_all_quotes(u.name))) for u in userset)

    # find all the quotes that contain the fragment
    matches = (q for q in allquotes if fragment.lower() in q[1].lower())

    # sort the matches by similarity
    matches = sorted(matches, key=lambda q: character_distance(fragment.lower(), q[1].lower()))

    # re-sort the matches by exact word match
    matches = sorted(matches, key=lambda q: 0 if f" {fragment} " in q[1] else 1)

    # select the first N matches
    matches = matches[:n]

    # format the matches into a string for sending
    matchstr = "\n".join(f"{i+1}. {q[0]}: {q[1].strip()}" for i, q in enumerate(matches))

    if len(matches) == 0:
        await send(msg, "No matches found.")
    else:
        suffix = 'es' if len(matches) != 1 else ''
        await send(msg, f"Found {len(matches)} match{suffix} for \"{fragment}\":\n{matchstr}")

manuals["sethindsight"] = f"""
Usage:
{CMDCHAR}sethindsight [num]
Sets the markov hindsight to num.
Only numbers between 1 and 3 are valid.
"""
aliases["sethindsight"].append("shs")
async def sethindsight(msg, tail):
    global hindsight
    strnum, *_ = tail
    num = int(strnum)
    if num < 1 or num > 3:
        return
    
    hindsight = num

    regenerate_models(markov_models, usernames_as_strs(userset), hindsight)

    await send(msg, f"Successfully set markov hindsight to {hindsight}")

def maybe_regen_markov():
    global markov_models
    global time_since_model_refresh
    do_regen = len(markov_models) == 0 or time_since_model_refresh > REFRESH_MODEL_THRESHOLD

    if do_regen:
        regenerate_models(markov_models, usernames_as_strs(userset))
        time_since_model_refresh = 0
    else:
        time_since_model_refresh += 1


def everyone_model() -> NewlineText:
    return typing.cast(
        NewlineText, 
        markovify.combine(list(markov_models.values())))


def fetch_model(name: str) -> NewlineText:
    if name == "everyone":
        return everyone_model()
    return markov_models[name]

manuals["genquote"] = f"""
Usage:
{CMDCHAR}genquote [name]
Generates a quote from the specified user's past quotes using a markov chain model.
"""
aliases["genquote"].append("gq")
async def genquote(msg: Message, tail: "list[str]"):
    if tail == []:
        name = "anyone"
        n = 1
    elif len(tail) == 1:
        name, *_ = tail
        n = 1
    else:
        name, strn, *_ = tail
        n = int(strn)
    
    if n > 5:
        await send(msg, "You may only request up to five sequential quotes.")
        return

    name = await handle_name(msg, name) if name not in ("everyone", "anyone") else name 
    if name == None: return

    maybe_regen_markov()

    names = [weighted_choice(user_quote_distribution) if name == "anyone" else name for _ in range(n)]
    names_maybe_quotes = ((x, generate_quote(fetch_model(x))) for x in names)

    isnotnone = lambda x: x[1] is not None

    quotes = [f"{x}: \"{q}\"" for x, q in filter(
        isnotnone, names_maybe_quotes)]

    await send(msg, "\n".join(quotes))
    return True

manuals["eightball"] = f"""
Usage:
{CMDCHAR}eightball [question...]
Returns a random answer to the specified question.
"""
aliases["eightball"].append("8ball")
async def eightball(msg: Message, tail: "list[str]"):
    if tail == []:
        await send(msg, "You have to specify a question to ask the magic 8ball.")
        return

    question = " ".join(tail)
    qres = question.strip('?\n ')
    await send(msg, f"{qres}?\n🎱 {choice(ANSWERS)}")

manuals["ballsdeep"] = f"""
Usage:
{CMDCHAR}ballsdeep
This is a dumb function.
"""
async def ballsdeep(msg: Message):
    await send(msg, "[SUCCESSFULLY HACKED FBI - BLOWING UP COMPUTER]")
    for i in range(5, 0, -1):
        await send(msg, f"{i}")

def alias_lookup(cmd: str) -> Optional[str]:
    for key, alias_list in aliases.items():
        if cmd in alias_list:
            return key
    return None


manuals["manual"] = f"""
Usage:
{CMDCHAR}manual [command]
Sends the specified command's manual.
"""
aliases["manual"].append("man")
async def manual(msg: Message, tail: "list[str]"):
    cmd, *_ = tail
    
    if cmd not in manuals:
        if cmd not in chain.from_iterable(aliases.values()):
            await send(msg, f"{cmd} is not a command.")
            return
        else:
            cmd = alias_lookup(cmd)
    
    if cmd is None:
        await send(msg, "ping cosmo, something's fucked up in man")
        return

    manual = manuals[cmd].strip()

    alias_list = aliases[cmd]
    alias_part = f"\n\nAliases: [{', '.join(alias_list)}]" if alias_list != [] else ""
    
    await send(msg, f"```{manual} {alias_part}```")

manuals["commands"] = f"""
Usage:
{CMDCHAR}commands
Sends all the commands that ZeroAI supports.
"""
aliases["commands"].append("cmds")
async def commands(msg: Message):
    nwln = '\n'
    cmdnames = sorted(manuals)
    names_plus_aliases = [
        f"{name} [{', '.join(aliases[name])}]" if len(aliases[name])>0 else f"{name}" 
        for name in cmdnames]
    string = f"Commands:\n```{nwln.join(names_plus_aliases)}```"
    await send(msg, string)

manuals["users"] = f"""
Usage:
{CMDCHAR}users
Shows all the currently registered users of the bot.
Defaults to only showing users with registered Discord uids.
Pass the -all flag to show users without Discord uids.
"""
async def users(msg: Message, text: "list[str]"):
    showall = True
    if "-all" not in text:
        showall = False
    usernames = sorted([u.name for u in userset if not u.isnull or showall])
    await send(msg, f"Users:\n [{', '.join(usernames)}]")

manuals["congratulate"] = f"""
Usage:
{CMDCHAR}congratulate [name]
Congratulates the specified person!
"""
aliases["congratulate"].append("gratz")
async def congratulate(msg: Message, tail: "list[str]"):
    text = " ".join(tail)
    if text.strip() == "":
        await send(msg, "You have to specify a person to congratulate.")
        return

    await send(msg, f"well done {text}!")

manuals["adduser"] = f"""
Usage:
{CMDCHAR}adduser name
Adds the specified user to the bot's user database.
"""
aliases["eval"].append("au")
async def adduser(msg: Message, tail: "list[str]"):
    if len(tail) != 1:
        await send(msg, "You must specify a name that contains no spaces.")
        return

    name = tail[0].lower()
    if name in userset:
        await send(msg, f"{name} is already registered.")
        return
    
    user = UserData.dummy_from_name(name)
    userset.add(user)
    write_users(userset)
    # add QUOTEPATH/namequotes.txt
    filename = QUOTEPATH + name + "quotes.txt"
    with open(filename, "w") as f:
        f.write("")
    await send(msg, f"{name} has been registered.")

manuals["cock"] = f"""
Usage:
{CMDCHAR}cock
Explains all about John Green's favourite taste.
"""
async def cock(msg: Message):
    await send(msg, "As I near 200,000 followers here at fishingboatproceeds, I just wanted to to say cock is one of my favorite tastes. Not only that, but balls smell amazing. It makes me go a little crazy on it to be honest. Like, I cannot get it far enough down my throat to be satisfied. I’m only satisfied when I feel those intense, powerful, salty hot pumps of cum down my throat. When I sit back on my heels, look up at you with cum all over my mouth and slobber running down my neck, hair all fucked up and wipe my mouth with the back of my arm and ask you if I did a good job and you cannot even speak because I’ve drained all of your energy out the tip of your dick..... that’s when I’m satisfied.")

manuals["wednesday"] = f"""
Usage:
{CMDCHAR}wednesday
What a week, huh?
"""
aliases["wednesday"].append("wed")
aliases["wednesday"].append("whataweek")
async def wednesday(msg: Message):
    await send(msg, "https://cdn.discordapp.com/attachments/588844070315622410/1014434813761028136/20220323_114006-4.jpg")

manuals["bash"] = f"""
Usage:
{CMDCHAR}bash [command(s)]
Executes bash commands. Don't use this if you aren't cosmo.
"""
async def bash(msg: Message, tail: "list[str]"):
    sender: Any = msg.author
    name = user_find(sender.name, sender.discriminator)
    if name != "cosmo":
        await send(msg, "You are not cosmo.")
        return

    cmd = " ".join(tail)
    await send(msg, f"Executing `{cmd}`...")
    try:
        text = subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError as e:
        text = f"ERROR:\n{e.output.decode('utf-8')}"
    text = text[:1800]
    await send(msg, f"```\n{text}\n```")

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
