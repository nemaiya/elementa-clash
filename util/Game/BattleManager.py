

from util.Game.Player import Player


class BattleManager():
    def __init__(self, player1: Player, player2: Player, is_player_turn: bool) -> None:
        self.player1: Player = player1
        self.player2: Player = player2

        self.round: int = 1
        self.turn: int = 1

        self.is_player_turn: bool = is_player_turn

    