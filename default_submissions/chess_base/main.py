import random

import chess

import ai


def make_ai_move(board: chess.Board):
    board_copy = chess.Board(board.fen(), chess960=True)
    move = ai.make_move(board_copy, 10.0)  # Change this float if you want to test your AI under time pressure

    if isinstance(move, str):
        move = chess.Move.from_uci(move)

    return move


def main():
    board = chess.Board.from_chess960_pos(random.randint(0, 959))
    print()
    print("Enter moves in UCI form, for example to move your pawn from e2 to e4, you should type the string 'e2e4'")
    print("For a promotion of a pawn on e7 to a queen on e8 you should type the string 'e7e8q'")
    print()

    user_turn = random.random() < 0.5
    if user_turn:
        print("Playing White")
    else:
        print("Playing Black")

    while not board.is_game_over():
        move = None
        if user_turn:
            print()
            print(board)
            print()
            while move is None:
                try:
                    move = chess.Move.from_uci(input("Enter move: "))
                    if move not in board.legal_moves:
                        print("Invalid Move!")
                        move = None
                except ValueError as e:
                    print(e)
                    move = None

        else:
            move = make_ai_move(board)

        board.push(move)
        user_turn = not user_turn


if __name__ == "__main__":
    main()
