import discord
from os import getenv
from dotenv import load_dotenv

import chess.svg
from Glyph import State
from chess import Board, Move
from viri.Viridithas import Viridithas
from random import choice, random

TICTACTOE_RUNNING = False
CHESS_RUNNING = False

HELP_TEXT = """My commands are:
play [ttt, tictactoe, tic-tac-toe, noughts-and-crosses]
play [chess]."""

load_dotenv()

token = getenv('TOKEN')

TTT_GAME = State()
CHESS_GAME = Board()
CHESS_ENGINE = Viridithas(human=False, fen=CHESS_GAME.fen(), pgn='', timeLimit=15,
                          fun=False, contempt=3000, book=True, advancedTC=[])

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global TICTACTOE_RUNNING
    global CHESS_RUNNING
    global CHESS_GAME
    global TTT_GAME
    if message.author == client.user:
        return
    print(message.content)
    if TICTACTOE_RUNNING and message.content.split()[0].lower() == "move" and message.content.split()[1] in "123456789":
        TTT_GAME.play(int(message.content.split()[1])-1)
        await message.channel.send(f"```\n{TTT_GAME.__repr__()}\n```")
        if TTT_GAME.is_game_over():
            await message.channel.send(TTT_GAME.show_result_as_str())
        if TTT_GAME.is_game_over():
            await message.channel.send(TTT_GAME.show_result_as_str())
    elif TICTACTOE_RUNNING and message.content[0].lower() == "move" and message.content[1] == "resign":
        await message.channel.send("1-0")

    if CHESS_RUNNING and message.content.split()[0].lower() == "move":
        try:
            await viridithas_engine_move(message)

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

            await play_function_map.get(args[2], not_programmed)(message)

        elif args[1] == "pieces":
            await message.channel.send(choose_three_pieces())
        else:
            await message.channel.send('Invalid command.')


async def viridithas_engine_move(message):
    global CHESS_GAME
    move: Move = CHESS_GAME.parse_san(message.content.split()[1])

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
        f"The board after Viri's move:```\n{CHESS_GAME.unicode()}\n```\n{CHESS_ENGINE.last_search}")

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
