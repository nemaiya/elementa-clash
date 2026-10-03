from .Player import Player, DeckData

class BattlePlayer:
    def __init__(self, player: Player, deck: DeckData) -> None:
        self.player: Player = player
        self.deck: DeckData = deck