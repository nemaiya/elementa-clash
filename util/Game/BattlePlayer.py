from util.Game.Player import DeckData


from util.Game.Card import ACTION_DB, CHARACTER_DB

from .Player import Player, DeckData, UserInfo
from util.Game.Card import ActionCard, CharacterCard, CostType, ElementalTypes
import random

# Every die has one face per element plus an Omni face, which can pay for any element.
DIE_FACES: list[ElementalTypes] = ["omni", "pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo"]
DICE_PER_ROLL: int = 16
MAX_HAND_SIZE: int = 10
MAX_SUPPORTS: int = 4
SWITCH_COST: int = 1


class BattlePlayer:
    def __init__(self, player: Player, deck: DeckData) -> None:
        self.player: Player = player
        self.deck: DeckData = deck

        self.list_of_action_cards: list[ActionCard] = []
        self.list_of_characters: list[CharacterCard] = []
        # Cards currently held. The opening hand is dealt from the deck into here.
        self.hand: list[ActionCard] = []
        # Index into list_of_characters of the character currently fighting.
        self.active_character_index: int | None = None
        self.dice: list[ElementalTypes] = []
        self.supports: list[ActionCard] = []
        self.summons: list[dict[str, object]] = []
        self.winery_used_this_round: bool = False

        self.setup_list_of_action_cards()
        self.setup_list_of_characters()
    
    def setup_list_of_action_cards(self) -> list[ActionCard]:
        for action_card in self.deck["action_cards"]:
            self.list_of_action_cards.append(ActionCard(action_card))
        return self.list_of_action_cards
    
    def setup_list_of_characters(self) -> list[CharacterCard]:
        for character in self.deck["characters"]:
            self.list_of_characters.append(CharacterCard(character))
        return self.list_of_characters

    def get_list_of_random_action_cards(self, number_of_cards: int = 4) -> list[ActionCard]:
        return random.sample(self.list_of_action_cards, k=number_of_cards)

    def draw_cards(self, number_of_cards: int) -> list[ActionCard]:
        """Take cards out of the remaining deck so they cannot be drawn again."""
        number_of_cards = min(number_of_cards, len(self.list_of_action_cards))
        if number_of_cards <= 0:
            return []

        drawn: list[ActionCard] = random.sample(self.list_of_action_cards, k=number_of_cards)
        for card in drawn:
            self.list_of_action_cards.remove(card)
        return drawn

    def draw_starting_hand(self, number_of_cards: int = 4) -> list[ActionCard]:
        self.hand = self.draw_cards(number_of_cards=number_of_cards)
        return self.hand

    def draw_to_hand(self, number_of_cards: int) -> list[ActionCard]:
        """Draws into the hand without going over MAX_HAND_SIZE; extra cards stay in the deck."""
        space: int = max(0, MAX_HAND_SIZE - len(self.hand))
        drawn: list[ActionCard] = self.draw_cards(number_of_cards=min(number_of_cards, space))
        self.hand.extend(drawn)
        return drawn

    def switch_cards(self, indexes: list[int]) -> None:
        """Put the chosen hand cards back into the deck and draw replacements."""
        valid: list[int] = list(dict.fromkeys(index for index in indexes if 0 <= index < len(self.hand)))
        if not valid:
            return

        # Draw first so a switched card is not immediately dealt back into the same slot.
        replacements: list[ActionCard] = self.draw_cards(number_of_cards=len(valid))
        returned: list[ActionCard] = []
        for slot, new_card in zip(valid, replacements):
            returned.append(self.hand[slot])
            self.hand[slot] = new_card
        self.list_of_action_cards.extend(returned)

    def switch_random_cards(self) -> None:
        """Used by the hidden opponent. Each card is switched or kept at random."""
        if not self.hand:
            return
        chosen: list[int] = [index for index in range(len(self.hand)) if random.random() < 0.5]
        self.switch_cards(indexes=chosen)

    @property
    def active_character(self) -> CharacterCard | None:
        if self.active_character_index is None:
            return None
        return self.list_of_characters[self.active_character_index]

    def set_active_character(self, index: int) -> None:
        if not 0 <= index < len(self.list_of_characters):
            raise IndexError(f"No character at index {index}.")
        if self.list_of_characters[index].current_hp <= 0:
            raise ValueError(f"{self.list_of_characters[index].name} is defeated and cannot be active.")
        self.active_character_index = index

    def choose_random_active_character(self) -> int:
        """Used by the bot. Picks any character that is still alive."""
        alive: list[int] = [index for index, character in enumerate(self.list_of_characters) if character.current_hp > 0]
        index: int = random.choice(alive)
        self.set_active_character(index=index)
        return index

    def roll_dice(self, number_of_dice: int = DICE_PER_ROLL) -> list[ElementalTypes]:
        self.dice = [random.choice(DIE_FACES) for _ in range(number_of_dice)]
        self.sort_dice()
        return self.dice

    def reroll_dice(self, indexes: list[int]) -> list[int]:
        """Rerolls the dice at the given indexes and returns the indexes that were rerolled."""
        valid: list[int] = sorted(set(index for index in indexes if 0 <= index < len(self.dice)))
        for index in valid:
            self.dice[index] = random.choice(DIE_FACES)
        return valid

    def team_elements(self) -> list[ElementalTypes]:
        return [character.element for character in self.list_of_characters if character.current_hp > 0]

    def sort_dice(self) -> None:
        """Omni first, then the active character's element, then the rest of the team, then everything else."""
        active: CharacterCard | None = self.active_character
        team: list[ElementalTypes] = self.team_elements()

        def priority(die: ElementalTypes) -> tuple[int, int]:
            if die == "omni":
                rank = 0
            elif active is not None and die == active.element:
                rank = 1
            elif die in team:
                rank = 2
            else:
                rank = 3
            return rank, DIE_FACES.index(die)

        self.dice.sort(key=priority)

    def choose_dice_to_keep(self) -> list[int]:
        """Used by the bot. Keeps Omni dice and any die matching an element in its team."""
        team: list[ElementalTypes] = self.team_elements()
        return [index for index, die in enumerate(self.dice) if die == "omni" or die in team]

    def alive_indexes(self) -> list[int]:
        return [index for index, character in enumerate(self.list_of_characters) if character.is_alive]

    def is_defeated(self) -> bool:
        return not self.alive_indexes()

    def add_dice(self, faces: list[ElementalTypes]) -> None:
        self.dice.extend(faces)
        self.sort_dice()

    def has_support(self, card_id: str) -> bool:
        return any(card.card_id == card_id for card in self.supports)

    def switch_discount(self) -> int:
        if self.winery_used_this_round:
            return 0
        if any(card.card_id == "dawn_winery" for card in self.supports):
            return 1
        return 0

    def reset_round_flags(self) -> None:
        self.winery_used_this_round = False
        for character in self.list_of_characters:
            character.reset_round_flags()

    def choose_payment(self, cost: dict[CostType, int], reductions: dict[str, int] | None = None) -> list[int] | None:
        """Return dice indexes that pay the cost, or None if the player cannot afford it."""
        reductions = reductions or {}
        remaining: list[tuple[int, ElementalTypes]] = list(enumerate(self.dice))
        spent: list[int] = []

        def take(predicate) -> int | None:
            for slot, (index, face) in enumerate(remaining):
                if predicate(face):
                    remaining.pop(slot)
                    spent.append(index)
                    return index
            return None

        elemental_needs: dict[str, int] = {}
        for face, amount in cost.items():
            if face in ("unaligned", "energy", "matching"):
                continue
            elemental_needs[face] = max(0, int(amount) - reductions.get(face, 0))

        for face, amount in elemental_needs.items():
            for _ in range(amount):
                if take(lambda die, needed=face: die == needed) is None:
                    if take(lambda die: die == "omni") is None:
                        return None

        unaligned: int = max(0, int(cost.get("unaligned", 0)) - reductions.get("unaligned", 0))
        for _ in range(unaligned):
            if take(lambda die: True) is None:
                return None
        return spent

    def spend_dice(self, indexes: list[int]) -> None:
        for index in sorted(set(indexes), reverse=True):
            if 0 <= index < len(self.dice):
                del self.dice[index]
        self.sort_dice()

    def try_pay(self, cost: dict[CostType, int], reductions: dict[str, int] | None = None) -> bool:
        payment: list[int] | None = self.choose_payment(cost=cost, reductions=reductions)
        if payment is None:
            return False
        self.spend_dice(indexes=payment)
        return True


    

class OtherBattlePlayer(BattlePlayer):
    def __init__(self, bot: bool = True) -> None:
        self.player: Player
        self.deck: DeckData
        self.get_player_info(bot=bot)

        super().__init__(player=self.player, deck=self.deck)
    
    def get_player_info(self, bot: bool = True) -> None:
        if bot:
            # Pick 3 unique characters
            bot_characters: list[str] = random.sample([key for key in CHARACTER_DB.keys()] , k=3)
            
            # Pick 10 action cards (using choices allows for duplicate cards in the deck; 
            # if they must be strictly unique, change 'choices' to 'sample')
            bot_action_cards: list[str] = random.choices([key for key in ACTION_DB.keys()], k=10)

            # Construct the mock deck
            bot_deck: DeckData = DeckData(user_id="0", uid="1", name="Bot Deck", characters=bot_characters, action_cards=bot_action_cards)

            # Construct the fake Player class
            self.player: Player = Player(
                uid="0", 
                username="Bot", 
                user_info=UserInfo(uid="0", xp=1, battle_wins=0, total_battles=0, active_deck_uid="1", deck_list_uid=["1"]),
                user_decks=[bot_deck]
            )
            
            # Store the active deck reference to match standard BattlePlayer behavior
            self.deck: DeckData = bot_deck