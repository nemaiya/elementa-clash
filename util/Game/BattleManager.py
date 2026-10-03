from util.Game.engine.game_model import GameModel
from util.Game.Player import Player


class BattleManager:
    def __init__(self, player1: Player, player2: Player, is_player_turn: bool) -> None:
        self.player1: Player = player1
        self.player2: Player = player2
        self.model: GameModel = GameModel()
        if not is_player_turn:
            self.model.current_player = 1
        self.round: int = self.model.round_number
        self.turn: int = 1
        self.is_player_turn: bool = is_player_turn
