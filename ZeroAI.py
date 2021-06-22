import discord
from os import getenv
from dotenv import load_dotenv

import chess.svg
from chess import Board, Move
from random import choice, random

COMMAND_CHARACTER = '!'

lads = {"finegold", "gotham", "jamie", "kit", "mike", "cosmo",
        "edward", "marina", "tegan", "elyn", "roman"}

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

@client.event
async def on_message(msg):
    if msg.author == client.user: return

    global TICTACTOE_RUNNING
    global CHESS_RUNNING
    global CHESS_GAME
    global TTT_GAME

    lead_char, cmd = process(msg.content)
    if lead_char != COMMAND_CHARACTER: return
    if len(cmd) == 0: return

    print(cmd)

    head, *tail = cmd

    if head == "pieces":
        pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
        content = ", ".join([choice(pieces) for i in range(3)])
        await send(msg, content)
    if head == "quote":
        assert len(tail) >= 1
        name, *_ = tail
        filename = name + "quotes.txt"
        with open(filename, 'r') as f:
            qs = [strip_endline(q) for q in f]
        await send(msg, f"{name}: \"{choice(qs)}\"")
    if head == "addquote":
        assert len(tail) >= 2
        name, *quotelist = tail
        assert name in lads
        quote = " ".join(quotelist)
        filename = name + "quotes.txt"
        with open(filename, 'a') as f:
            f.write("\n")
            f.write(quote)
        await send(msg, f"added quote \"{quote}\" to file {filename}")

async def send(message, text):
    await message.channel.send(text)

def choose_three_pieces():
    return ", ".join([choice(["pawn", "knight", "bishop", "rook", "queen", "king"]) for _ in range(3)])

if __name__ == "__main__":
    client.run(token)
