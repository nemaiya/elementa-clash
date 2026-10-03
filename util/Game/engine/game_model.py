from __future__ import annotations

from copy import deepcopy
from random import Random

from util.Game.engine.actions import (
    Action,
    ConfirmMulligan,
    ConfirmReroll,
    ElementalTuning,
    EndRound,
    ForcedSwitch,
    PlayActionCard,
    SelectActive,
    SwitchCharacter,
    UseSkill,
)
from util.Game.engine.catalog import (
    ACTION_CATALOG,
    CHARACTER_CATALOG,
    P1_CHARACTERS,
    P2_CHARACTERS,
    SUMMON_CATALOG,
    starting_action_ids,
)
from util.Game.engine.dice import combo_pays, find_dice_payment
from util.Game.engine.entities import ActionCardState, CharacterState, PlayerState, SummonState
from util.Game.engine.types import (
    DICE_FACES,
    CostKey,
    Phase,
    PlayerId,
    SkillKind,
)

HAND_LIMIT = 10
ZONE_LIMIT = 4
DICE_COUNT = 8
STARTING_HAND = 5
END_PHASE_DRAW = 2


class GameModel:
    """Pure rules state machine. No Pygame or network imports."""

    def __init__(self, rng: Random | None = None) -> None:
        self.rng: Random = rng if rng is not None else Random()
        self.round_number: int = 1
        self.phase: Phase = Phase.MULLIGAN
        self.current_player: PlayerId = 0
        self.first_ender: PlayerId | None = None
        self.winner: PlayerId | None = None
        self.forced_switch_player: PlayerId | None = None
        self.pending_force_swap: PlayerId | None = None
        self._end_phase_pending: list[PlayerId] = []
        self._in_end_phase: bool = False
        self.log: list[str] = []
        self.players: list[PlayerState] = [
            self._make_player(0, "Player 1", P1_CHARACTERS),
            self._make_player(1, "Player 2", P2_CHARACTERS),
        ]
        self._opening_draw()

    def _make_player(
        self,
        player_id: PlayerId,
        name: str,
        character_ids: tuple[str, str, str],
    ) -> PlayerState:
        characters = [CharacterState.from_def(CHARACTER_CATALOG[cid]) for cid in character_ids]
        deck = [ActionCardState.from_def(ACTION_CATALOG[cid]) for cid in starting_action_ids()]
        self.rng.shuffle(deck)
        return PlayerState(
            player_id=player_id,
            name=name,
            characters=characters,
            deck=deck,
            hand=[],
            supports=[],
            summons=[],
            dice=[],
        )

    def _opening_draw(self) -> None:
        for player in self.players:
            self._draw_cards(player, STARTING_HAND)
        self._log("Both players draw 5 action cards.")

    def _log(self, message: str) -> None:
        self.log.append(message)
        if len(self.log) > 40:
            del self.log[0:len(self.log) - 40]

    def opponent_id(self, player_id: PlayerId) -> PlayerId:
        return 1 if player_id == 0 else 0

    def player(self, player_id: PlayerId) -> PlayerState:
        return self.players[player_id]

    def waiting_on(self, player_id: PlayerId) -> bool:
        if self.phase == Phase.GAME_OVER:
            return False
        if self.phase == Phase.FORCED_SWITCH:
            return self.forced_switch_player == player_id
        if self.phase == Phase.MULLIGAN:
            return not self.player(player_id).mulligan_done
        if self.phase == Phase.SELECT_ACTIVE:
            return not self.player(player_id).active_selected
        if self.phase == Phase.REROLL:
            return not self.player(player_id).reroll_done
        if self.phase == Phase.ACTION:
            return (not self.player(player_id).ended_round) and self.current_player == player_id
        return False

    def snapshot(self) -> GameModel:
        return deepcopy(self)

    def apply(self, action: Action) -> bool:
        error = self.validate(action)
        if error is not None:
            self._log(f"Rejected: {error}")
            return False
        self.execute(action)
        return True

    def validate(self, action: Action) -> str | None:
        if self.phase == Phase.GAME_OVER:
            return "game is over"
        pid = action.player_id
        if pid not in (0, 1):
            return "invalid player"
        if self.phase == Phase.FORCED_SWITCH:
            if not isinstance(action, ForcedSwitch):
                return "must force-switch the fallen active character"
            if action.player_id != self.forced_switch_player:
                return "it is not your forced switch"
            return self._validate_forced_switch(action)

        if not self.waiting_on(pid) and not isinstance(action, ForcedSwitch):
            return "not this player's window"

        if isinstance(action, ConfirmMulligan):
            if self.phase != Phase.MULLIGAN:
                return "not mulligan phase"
            ids = {c.instance_id for c in self.player(pid).hand}
            if any(i not in ids for i in action.discard_instance_ids):
                return "discard is not in hand"
            return None
        if isinstance(action, SelectActive):
            if self.phase != Phase.SELECT_ACTIVE:
                return "not active-select phase"
            return self._validate_character_index(pid, action.character_index, must_be_alive=True)
        if isinstance(action, ConfirmReroll):
            if self.phase != Phase.REROLL:
                return "not reroll phase"
            n = len(self.player(pid).dice)
            if any(i < 0 or i >= n for i in action.die_indices):
                return "die index out of range"
            if len(set(action.die_indices)) != len(action.die_indices):
                return "duplicate die indices"
            return None
        if isinstance(action, UseSkill):
            if self.phase != Phase.ACTION:
                return "not action phase"
            return self._validate_use_skill(action)
        if isinstance(action, SwitchCharacter):
            if self.phase != Phase.ACTION:
                return "not action phase"
            return self._validate_switch(action)
        if isinstance(action, EndRound):
            if self.phase != Phase.ACTION:
                return "not action phase"
            if self.player(pid).ended_round:
                return "already ended round"
            return None
        if isinstance(action, PlayActionCard):
            if self.phase != Phase.ACTION:
                return "not action phase"
            return self._validate_play_card(action)
        if isinstance(action, ElementalTuning):
            if self.phase != Phase.ACTION:
                return "not action phase"
            return self._validate_tune(action)
        if isinstance(action, ForcedSwitch):
            return "forced switch is not required"
        return "unknown action"

    def execute(self, action: Action) -> None:
        if isinstance(action, ConfirmMulligan):
            self._do_mulligan(action)
        elif isinstance(action, SelectActive):
            self._do_select_active(action)
        elif isinstance(action, ConfirmReroll):
            self._do_reroll(action)
        elif isinstance(action, UseSkill):
            self._do_use_skill(action)
        elif isinstance(action, SwitchCharacter):
            self._do_switch(action)
        elif isinstance(action, EndRound):
            self._do_end_round(action)
        elif isinstance(action, PlayActionCard):
            self._do_play_card(action)
        elif isinstance(action, ElementalTuning):
            self._do_tune(action)
        elif isinstance(action, ForcedSwitch):
            self._do_forced_switch(action)

    def _validate_character_index(self, player_id: PlayerId, index: int, *, must_be_alive: bool) -> str | None:
        chars = self.player(player_id).characters
        if index < 0 or index >= len(chars):
            return "character index out of range"
        if must_be_alive and not chars[index].alive:
            return "character is defeated"
        return None

    def _validate_forced_switch(self, action: ForcedSwitch) -> str | None:
        player = self.player(action.player_id)
        err = self._validate_character_index(action.player_id, action.character_index, must_be_alive=True)
        if err:
            return err
        if action.character_index == player.active_index:
            return "must choose a different living character"
        return None

    def _find_card(self, player: PlayerState, instance_id: str) -> ActionCardState | None:
        for card in player.hand:
            if card.instance_id == instance_id:
                return card
        return None

    def adjusted_skill_cost(self, character: CharacterState, skill: SkillKind) -> dict[CostKey, int]:
        cost = dict(character.skill(skill).cost)
        equipment = character.equipment
        if (
            equipment is not None
            and equipment.defn.skill_cost_reduction_element is not None
            and not equipment.once_per_round_used
            and skill in ("normal", "skill", "burst")
        ):
            element = equipment.defn.skill_cost_reduction_element
            if cost.get(element, 0) > 0:
                cost[element] = cost[element] - 1
                if cost[element] <= 0:
                    del cost[element]
        return cost

    def _validate_payment(
        self,
        player: PlayerState,
        cost: dict[CostKey, int],
        die_indices: tuple[int, ...],
        energy: int,
    ) -> str | None:
        energy_cost = cost.get("energy", 0)
        if energy < energy_cost:
            return "not enough energy"
        n = len(player.dice)
        if any(i < 0 or i >= n for i in die_indices):
            return "die index out of range"
        if len(set(die_indices)) != len(die_indices):
            return "duplicate die indices"
        needed = sum(v for k, v in cost.items() if k != "energy")
        if len(die_indices) != needed:
            return "incorrect number of dice"
        if needed == 0:
            return None
        if not combo_pays(player.dice, die_indices, cost):
            return "selected dice do not pay the cost"
        return None

    def _validate_use_skill(self, action: UseSkill) -> str | None:
        player = self.player(action.player_id)
        active = player.active()
        if active is None or not active.alive:
            return "no living active character"
        if action.skill == "burst" and active.energy < active.max_energy:
            return "not enough energy for burst"
        cost = self.adjusted_skill_cost(active, action.skill)
        return self._validate_payment(player, cost, action.die_indices, active.energy)

    def switch_cost(self, player: PlayerState) -> dict[CostKey, int]:
        reduction = 0
        if not player.switch_discount_used:
            for support in player.supports:
                reduction += support.defn.switch_cost_reduction
        amount = max(0, 1 - reduction)
        if amount == 0:
            return {}
        return {"unaligned": amount}

    def _validate_switch(self, action: SwitchCharacter) -> str | None:
        player = self.player(action.player_id)
        err = self._validate_character_index(action.player_id, action.character_index, must_be_alive=True)
        if err:
            return err
        if action.character_index == player.active_index:
            return "already active"
        cost = self.switch_cost(player)
        return self._validate_payment(player, cost, action.die_indices, 0)

    def _validate_play_card(self, action: PlayActionCard) -> str | None:
        player = self.player(action.player_id)
        card = self._find_card(player, action.card_instance_id)
        if card is None:
            return "card not in hand"
        err = self._validate_payment(player, dict(card.defn.cost), action.die_indices, 0)
        if err:
            return err
        if card.kind == "equipment":
            if action.target_character_index is None:
                return "equipment needs a character target"
            terr = self._validate_character_index(
                action.player_id, action.target_character_index, must_be_alive=True
            )
            if terr:
                return terr
            target = player.characters[action.target_character_index]
            restriction = card.defn.restriction
            if restriction is not None and target.weapon != restriction:
                return f"only {restriction} users can equip this"
        elif card.kind == "event" and card.defn.heal > 0:
            if action.target_character_index is None:
                return "heal event needs a character target"
            terr = self._validate_character_index(
                action.player_id, action.target_character_index, must_be_alive=True
            )
            if terr:
                return terr
            if player.characters[action.target_character_index].food_used_this_round:
                return "that character already ate this round"
        return None

    def _validate_tune(self, action: ElementalTuning) -> str | None:
        player = self.player(action.player_id)
        if player.active() is None:
            return "no active character"
        if self._find_card(player, action.card_instance_id) is None:
            return "card not in hand"
        if action.die_index < 0 or action.die_index >= len(player.dice):
            return "die index out of range"
        active = player.active()
        assert active is not None
        if player.dice[action.die_index] == active.element:
            return "die is already the active element"
        return None

    def _spend_dice(self, player: PlayerState, indices: tuple[int, ...]) -> None:
        for i in sorted(indices, reverse=True):
            del player.dice[i]

    def _push_support(self, player: PlayerState, item: ActionCardState) -> None:
        if len(player.supports) >= ZONE_LIMIT:
            removed = player.supports.pop(0)
            self._log(f"Support zone full; oldest {removed.name} was overwritten.")
        player.supports.append(item)

    def _push_summon(self, player: PlayerState, item: SummonState) -> None:
        if len(player.summons) >= ZONE_LIMIT:
            removed = player.summons.pop(0)
            self._log(f"Summon zone full; oldest {removed.name} was overwritten.")
        player.summons.append(item)

    def _draw_cards(self, player: PlayerState, amount: int) -> None:
        drawn = 0
        while drawn < amount:
            if not player.deck:
                self._log(f"{player.name} deck is empty; no card drawn.")
                break
            card = player.deck.pop(0)
            if len(player.hand) >= HAND_LIMIT:
                self._log(f"{player.name} hand is full; {card.name} was destroyed.")
            else:
                player.hand.append(card)
            drawn += 1

    def _do_mulligan(self, action: ConfirmMulligan) -> None:
        player = self.player(action.player_id)
        discarded: list[ActionCardState] = []
        keep: list[ActionCardState] = []
        discard_set = set(action.discard_instance_ids)
        for card in player.hand:
            if card.instance_id in discard_set:
                discarded.append(card)
            else:
                keep.append(card)
        player.hand = keep
        self._draw_cards(player, len(discarded))
        player.deck.extend(discarded)
        self.rng.shuffle(player.deck)
        player.mulligan_done = True
        self._log(f"{player.name} mulliganed {len(discarded)} card(s).")
        if all(p.mulligan_done for p in self.players):
            self.phase = Phase.SELECT_ACTIVE
            self._log("Select starting active characters.")

    def _do_select_active(self, action: SelectActive) -> None:
        player = self.player(action.player_id)
        player.active_index = action.character_index
        player.active_selected = True
        active = player.active()
        assert active is not None
        self._log(f"{player.name} chose {active.name} as active.")
        if all(p.active_selected for p in self.players):
            self._enter_roll_phase()

    def _enter_roll_phase(self) -> None:
        self.phase = Phase.ROLL
        for player in self.players:
            player.dice = [self.rng.choice(DICE_FACES) for _ in range(DICE_COUNT)]
            player.reroll_done = False
        self.phase = Phase.REROLL
        self._log(f"Round {self.round_number}: both players rolled 8 dice.")

    def _do_reroll(self, action: ConfirmReroll) -> None:
        player = self.player(action.player_id)
        for i in action.die_indices:
            player.dice[i] = self.rng.choice(DICE_FACES)
        player.reroll_done = True
        self._log(f"{player.name} rerolled {len(action.die_indices)} die/dice.")
        if all(p.reroll_done for p in self.players):
            self._enter_action_phase()

    def _enter_action_phase(self) -> None:
        self.phase = Phase.ACTION
        starter: PlayerId = self.first_ender if self.first_ender is not None else 0
        self.current_player = starter
        self.first_ender = None
        for player in self.players:
            player.ended_round = False
            for support in list(player.supports):
                if support.defn.generate_omni > 0:
                    for _ in range(support.defn.generate_omni):
                        if len(player.dice) < 16:
                            player.dice.append("omni")
                    self._log(f"{support.name} created Omni dice for {player.name}.")
        self._log(f"Action Phase. {self.player(self.current_player).name} starts.")

    def _after_combat(self, player_id: PlayerId) -> None:
        if self.phase in (Phase.FORCED_SWITCH, Phase.GAME_OVER, Phase.END_PHASE):
            return
        opponent = self.opponent_id(player_id)
        if self.player(opponent).ended_round:
            return
        self.current_player = opponent

    def _do_use_skill(self, action: UseSkill) -> None:
        player = self.player(action.player_id)
        opponent = self.player(self.opponent_id(action.player_id))
        active = player.active()
        assert active is not None
        skill_def = active.skill(action.skill)
        cost = self.adjusted_skill_cost(active, action.skill)
        if (
            active.equipment is not None
            and active.equipment.defn.skill_cost_reduction_element is not None
            and dict(active.skill(action.skill).cost) != cost
        ):
            active.equipment.once_per_round_used = True
        self._spend_dice(player, action.die_indices)

        bonus = 0
        if active.equipment is not None:
            bonus = active.equipment.defn.damage_bonus
        self._deal_damage(opponent, skill_def.damage + bonus, piercing=False)
        if skill_def.piercing_damage > 0:
            self._deal_piercing(opponent, skill_def.piercing_damage)
        if skill_def.apply is not None:
            opp_active = opponent.active()
            if opp_active is not None and opp_active.alive:
                opp_active.applied_element = skill_def.apply
        if skill_def.shield > 0:
            active.shield += skill_def.shield
        if skill_def.heal_team > 0:
            for c in player.characters:
                if c.alive:
                    c.hp = min(c.max_hp, c.hp + skill_def.heal_team)
        if skill_def.summon_id is not None:
            sdef = SUMMON_CATALOG[skill_def.summon_id]
            self._push_summon(player, SummonState.from_def(sdef))
        if action.skill == "burst":
            if (
                active.equipment is not None
                and active.equipment.defn.energy_on_burst > 0
                and not active.equipment.once_per_round_used
            ):
                active.energy = 0
                active.energy = min(active.max_energy, active.equipment.defn.energy_on_burst)
                active.equipment.once_per_round_used = True
            else:
                active.energy = 0
        else:
            active.energy = min(active.max_energy, active.energy + skill_def.energy_gain)

        self._log(f"{player.name}'s {active.name} used {skill_def.name}.")
        if skill_def.force_swap:
            if opponent.alive_standby_indices() and opponent.active() is not None and opponent.active().alive:
                self.pending_force_swap = opponent.player_id
                self.forced_switch_player = opponent.player_id
                self.phase = Phase.FORCED_SWITCH
                self._log(f"{opponent.name} is knocked back and must switch.")
                return
        self._after_combat(action.player_id)

    def _deal_damage(self, victim: PlayerState, amount: int, *, piercing: bool) -> None:
        if amount <= 0:
            return
        active = victim.active()
        if active is None or not active.alive:
            return
        remaining = amount
        if not piercing and active.shield > 0:
            absorbed = min(active.shield, remaining)
            active.shield -= absorbed
            remaining -= absorbed
        active.hp = max(0, active.hp - remaining)
        if active.hp == 0:
            self._on_defeat(victim, victim.active_index if victim.active_index is not None else 0)

    def _deal_piercing(self, victim: PlayerState, amount: int) -> None:
        for i, character in enumerate(victim.characters):
            if i == victim.active_index or not character.alive:
                continue
            character.hp = max(0, character.hp - amount)
            if character.hp == 0:
                self._log(f"{character.name} was defeated by piercing damage.")
        if not victim.has_living_character():
            self._declare_winner(self.opponent_id(victim.player_id))

    def _on_defeat(self, victim: PlayerState, char_index: int) -> None:
        fallen = victim.characters[char_index]
        self._log(f"{fallen.name} has been defeated.")
        if not victim.has_living_character():
            self._declare_winner(self.opponent_id(victim.player_id))
            return
        if victim.active_index == char_index:
            self.phase = Phase.FORCED_SWITCH
            self.forced_switch_player = victim.player_id
            self._log(f"{victim.name} must choose a new active character.")

    def _declare_winner(self, player_id: PlayerId) -> None:
        self.winner = player_id
        self.phase = Phase.GAME_OVER
        self.forced_switch_player = None
        self._log(f"{self.player(player_id).name} wins.")

    def _do_switch(self, action: SwitchCharacter) -> None:
        player = self.player(action.player_id)
        had_discount = any(s.defn.switch_cost_reduction > 0 for s in player.supports) and not player.switch_discount_used
        self._spend_dice(player, action.die_indices)
        if had_discount:
            player.switch_discount_used = True
        player.active_index = action.character_index
        active = player.active()
        assert active is not None
        self._log(f"{player.name} switched to {active.name}.")
        self._after_combat(action.player_id)

    def _do_end_round(self, action: EndRound) -> None:
        player = self.player(action.player_id)
        player.ended_round = True
        if self.first_ender is None:
            self.first_ender = action.player_id
        self._log(f"{player.name} declared End Round.")
        if all(p.ended_round for p in self.players):
            self._begin_end_phase()
        else:
            self.current_player = self.opponent_id(action.player_id)

    def _begin_end_phase(self) -> None:
        self._in_end_phase = True
        order: list[PlayerId] = [0, 1]
        if self.first_ender == 1:
            order = [1, 0]
        self._end_phase_pending = order
        self._log("End Phase.")
        self._continue_end_phase()

    def _continue_end_phase(self) -> None:
        self.phase = Phase.END_PHASE
        while self._end_phase_pending:
            pid = self._end_phase_pending.pop(0)
            self._resolve_end_phase_player(pid)
            if self.phase == Phase.GAME_OVER:
                self._in_end_phase = False
                self._end_phase_pending = []
                return
            if self.phase == Phase.FORCED_SWITCH:
                return
        self._in_end_phase = False
        self.round_number += 1
        self._enter_roll_phase()

    def _resolve_end_phase_player(self, pid: PlayerId) -> None:
        player = self.player(pid)
        opponent = self.player(self.opponent_id(pid))
        for summon in list(player.summons):
            self._deal_damage(opponent, summon.defn.damage, piercing=False)
            if self.phase == Phase.GAME_OVER:
                return
            summon.usages -= 1
            self._log(f"{summon.name} dealt {summon.defn.damage} end-phase damage.")
        player.summons = [s for s in player.summons if s.usages > 0]
        if self.phase == Phase.GAME_OVER:
            return
        for support in player.supports:
            heal = support.defn.end_phase_heal_active
            active = player.active()
            if heal > 0 and active is not None and active.alive:
                active.hp = min(active.max_hp, active.hp + heal)
                self._log(f"{support.name} healed {active.name} for {heal}.")
        kept_supports: list[ActionCardState] = []
        for support in player.supports:
            if support.remaining_rounds > 0:
                support.remaining_rounds -= 1
                if support.remaining_rounds <= 0:
                    self._log(f"{support.name} expired.")
                    continue
            kept_supports.append(support)
        player.supports = kept_supports
        self._draw_cards(player, END_PHASE_DRAW)
        player.reset_round_flags()

    def _do_play_card(self, action: PlayActionCard) -> None:
        player = self.player(action.player_id)
        card = self._find_card(player, action.card_instance_id)
        assert card is not None
        self._spend_dice(player, action.die_indices)
        player.hand = [c for c in player.hand if c.instance_id != action.card_instance_id]
        if card.kind == "equipment":
            assert action.target_character_index is not None
            target = player.characters[action.target_character_index]
            target.equipment = card
            self._log(f"{player.name} attached {card.name} to {target.name}.")
        elif card.kind == "support":
            self._push_support(player, card)
            self._log(f"{player.name} played support {card.name}.")
        else:
            if card.defn.heal > 0 and action.target_character_index is not None:
                target = player.characters[action.target_character_index]
                target.hp = min(target.max_hp, target.hp + card.defn.heal)
                target.food_used_this_round = True
                self._log(f"{player.name} played {card.name}, healing {target.name}.")
            else:
                self._log(f"{player.name} played event {card.name}.")

    def _do_tune(self, action: ElementalTuning) -> None:
        player = self.player(action.player_id)
        active = player.active()
        assert active is not None
        player.hand = [c for c in player.hand if c.instance_id != action.card_instance_id]
        player.dice[action.die_index] = active.element
        self._log(f"{player.name} tuned a die to {active.element}.")

    def _do_forced_switch(self, action: ForcedSwitch) -> None:
        player = self.player(action.player_id)
        player.active_index = action.character_index
        self.forced_switch_player = None
        active = player.active()
        assert active is not None
        self._log(f"{player.name} switched to {active.name} (forced).")
        knockback = self.pending_force_swap == action.player_id
        self.pending_force_swap = None
        if self._in_end_phase and self.phase != Phase.GAME_OVER:
            self._continue_end_phase()
            return
        self.phase = Phase.ACTION
        if knockback:
            # Jean-style knockback is a combat action by the attacker; resume opponent turn skip.
            attacker = self.opponent_id(action.player_id)
            self._after_combat(attacker)
        elif not player.ended_round:
            self.current_player = player.player_id
        else:
            self.current_player = self.opponent_id(player.player_id)

    def suggest_payment(self, player_id: PlayerId, cost: dict[CostKey, int]) -> list[int] | None:
        return find_dice_payment(self.player(player_id).dice, cost)

    def to_public_dict(self) -> dict[str, object]:
        def card_dict(card: ActionCardState) -> dict[str, object]:
            return {"id": card.instance_id, "name": card.name, "kind": card.kind}

        def char_dict(c: CharacterState) -> dict[str, object]:
            return {
                "name": c.name,
                "element": c.element,
                "hp": c.hp,
                "max_hp": c.max_hp,
                "energy": c.energy,
                "max_energy": c.max_energy,
                "weapon": c.weapon,
                "alive": c.alive,
            }

        return {
            "round": self.round_number,
            "phase": self.phase.value,
            "current_player": self.current_player,
            "winner": self.winner,
            "players": [
                {
                    "name": p.name,
                    "active_index": p.active_index,
                    "ended_round": p.ended_round,
                    "dice": list(p.dice),
                    "hand": [card_dict(c) for c in p.hand],
                    "characters": [char_dict(c) for c in p.characters],
                    "supports": [card_dict(s) for s in p.supports],
                    "summons": [{"name": s.name, "usages": s.usages} for s in p.summons],
                    "deck_count": len(p.deck),
                }
                for p in self.players
            ],
        }
