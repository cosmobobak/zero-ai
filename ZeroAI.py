import discord
from os import getenv
from dotenv import load_dotenv

import chess.svg
from Glyph import State
from chess import Board, Move
from viridithas_chess.src.Viridithas import Viridithas
from random import choice, random

COMMAND_CHARACTER = '!'

TICTACTOE_RUNNING = False
CHESS_RUNNING = False

lads = {"finegold", "gotham", "jamie", "kit", "mike", "cosmo",
        "edward", "marina", "tegan", "elyn", "roman"}

HELP_TEXT = """My commands are:
play [ttt, tictactoe, tic-tac-toe, noughts-and-crosses]
play [chess]."""

load_dotenv()

token = getenv('TOKEN')

TTT_GAME = State()
CHESS_GAME = Board()
CHESS_ENGINE = Viridithas(
    human=False, 
    fen=CHESS_GAME.fen(), 
    pgn='', 
    timeLimit=15,
    book=True,
    fun=True,  
    contempt=3000)

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

async def viridithas_engine_move(message, message_content):
    global CHESS_GAME
    move: Move = CHESS_GAME.parse_san(message_content[1])

    CHESS_GAME.push(move)
    CHESS_ENGINE.node.push(move)

    await message.channel.send(
        f"The board after your move:\n```\n{CHESS_GAME.unicode()}\n```")

    if CHESS_GAME.is_game_over():
        await message.channel.send(CHESS_GAME.result())
    
    await message.channel.send("Starting to think!")
    move = CHESS_ENGINE.engine_move()
    await message.channel.send("Finished thinking.")
    CHESS_GAME.push(move)

    await message.channel.send(
        f"The board after Viri's move:```\n{CHESS_GAME.unicode()}\n```\n{CHESS_ENGINE.last_search()}")

    if CHESS_GAME.is_game_over():
        await message.channel.send(CHESS_GAME.result())

async def not_programmed(message):
    return await message.channel.send('I am not programmed to play that game.')

async def run_ttt(message):
    global TTT_GAME
    global TICTACTOE_RUNNING
    await message.channel.send('A nice game of noughts and crosses.')
    TTT_GAME = State()
    await message.channel.send(f"```\n{TTT_GAME.__repr__()}\n```")
    TICTACTOE_RUNNING = True

async def run_chess(message):
    global CHESS_RUNNING
    await message.channel.send('A nice game of chess.')
    CHESSgame = Board()
    await message.channel.send(f"```\n{CHESSgame.unicode()}\n```\nType \"move [san]\" to make a move.")
    CHESS_RUNNING = True

def choose_three_pieces():
    return ", ".join([choice(["pawn", "knight", "bishop", "rook", "queen", "king"]) for _ in range(3)])

if __name__ == "__main__":
    client.run(token)
