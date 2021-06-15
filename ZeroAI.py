import discord
from os import getenv
from dotenv import load_dotenv

import chess.svg
from Glyph import State
from chess import Board, Move
from Viridithas import Viridithas
from random import choice, random

TICTACTOE_RUNNING = False
CHESS_RUNNING = False

HELP_TEXT = """My commands are:
play [ttt, tictactoe, tic-tac-toe, noughts-and-crosses]
play [chess]."""

load_dotenv()

token = getenv('TOKEN')

TTTgame = State()
CHESSgame = Board()

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global TICTACTOE_RUNNING
    global CHESS_RUNNING
    global CHESSgame
    global TTTgame
    if message.author == client.user:
        return
    print(message.content)
    if TICTACTOE_RUNNING and message.content.split()[0].lower() == "move" and message.content.split()[1] in "123456789":
        TTTgame.play(int(message.content.split()[1])-1)
        await message.channel.send(f"```\n{TTTgame.__repr__()}\n```")
        if TTTgame.is_game_over():
            await message.channel.send(TTTgame.show_result_as_str())
        if TTTgame.is_game_over():
            await message.channel.send(TTTgame.show_result_as_str())
    elif TICTACTOE_RUNNING and message.content[0].lower() == "move" and message.content[1] == "resign":
        await message.channel.send("1-0")

    if CHESS_RUNNING and message.content.split()[0].lower() == "move":
        try:
            move = CHESSgame.parse_san(message.content.split()[1])
            CHESSgame.push(move)
            await message.channel.send(f"```\n{CHESSgame.unicode()}\n```")
            if CHESSgame.is_game_over():
                await message.channel.send(CHESSgame.result())
            engine = Viridithas(human=False, fen=CHESSgame.fen(), pgn='', timeLimit=15,
                                fun=False, contempt=3000, book=True, advancedTC=[])
            move = engine.engine_move()
            CHESSgame.push(move)
            await message.channel.send(f"```\n{CHESSgame.unicode()}\n```")
            if CHESSgame.is_game_over():
                await message.channel.send(CHESSgame.result())

        except AssertionError:
            await message.channel.send("invalid move.")

    if message.content.lower().startswith('computer,'):
        args = [x.lower() for x in message.content.split()]
        if args[1] == "help":

            await message.channel.send(HELP_TEXT)
        elif args[1] == "play":
            play_function_map = dict()
            play_function_map["chess"] = run_chess
            for c in ["ttt", "tictactoe", "tic-tac-toe", "noughts-and-crosses"]:
                play_function_map[c] = run_ttt

            play_function_map.get(args[2], default=not_programmed)(message)

        elif args[1] == "pieces":
            await message.channel.send(choose_three_pieces())
        else:
            await message.channel.send('Invalid command.')

async def not_programmed(message):
    return await message.channel.send('I am not programmed to play that game.')

async def run_ttt(message):
    global TICTACTOE_RUNNING
    await message.channel.send('A nice game of noughts and crosses.')
    TTTgame = State()
    await message.channel.send(f"```\n{TTTgame.__repr__()}\n```")
    TICTACTOE_RUNNING = True

async def run_chess(message):
    global CHESS_RUNNING
    await message.channel.send('A nice game of chess.')
    CHESSgame = Board()
    await message.channel.send(f"```\n{CHESSgame.unicode()}\n```")
    CHESS_RUNNING = True

def choose_three_pieces():
    return ", ".join([choice(["pawn", "knight", "bishop", "rook", "queen", "king"]) for _ in range(3)])

if __name__ == "__main__":
    client.run(token)
