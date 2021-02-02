import discord
import os

import chess.svg
from Glyph import State
from chess import Board, Move
from Viridithas import Viridithas


TICTACTOE_RUNNING = False
CHESS_RUNNING = False

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

    if TICTACTOE_RUNNING and message.content[0].lower() == "move" and message.content[1] in "123456789":
        TTTgame.play(int(message.content[0])-1)
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

        except Exception:
            await message.channel.send("invalid move.")

    if message.content.lower().startswith('computer,'):
        args = [x.lower() for x in message.content.split()]
        if args[1] == "help":
            await message.channel.send('My commands are:\n play [ttt, tictactoe, tic-tac-toe, noughts-and-crosses]\n play [chess].')
        elif args[1] == "play":
            if args[2] not in ["chess", "ttt", "tictactoe", "tic-tac-toe", "noughts-and-crosses", "connect-4", "uttt"]:
                await message.channel.send('I am not programmed to play that game.')
            elif args[2] in ["ttt", "tictactoe", "tic-tac-toe", "noughts-and-crosses"]:
                await message.channel.send('A nice game of noughts and crosses.')
                TTTgame = State()
                await message.channel.send(f"```\n{TTTgame.__repr__()}\n```")
                TICTACTOE_RUNNING = True
            elif args[2] in ["chess"]:
                await message.channel.send('A nice game of chess.')
                CHESSgame = Board()
                await message.channel.send(f"```\n{CHESSgame.unicode()}\n```")
                CHESS_RUNNING = True
        else:
            await message.channel.send('Invalid command.')


# client.run(os.getenv('TOKEN'))
client.run("ODAxNzYzODkwMDQzMDI3NDU2.YAlazw.kHrSRqli72lM1wp1i_i_Y-d6jgg")
