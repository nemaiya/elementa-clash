from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from util.Game.BattlePlayer import SWITCH_COST, BattlePlayer
from util.Game.Card import ActionCard, CharacterCard, CostType, ElementalTypes, SkillModel


SkillKey = Literal["normal", "skill", "burst"]
AuraElement = Literal["pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo"]

WEAPON_RESTRICTIONS: dict[str, str] = {
    "catalyst_user": "catalyst",
    "bow_user": "bow",
    "claymore_user": "claymore",
    "polearm_user": "polearm",
    "sword_user": "sword",
}

REACTION_NAMES: dict[frozenset[str], str] = {
    frozenset({"pyro", "hydro"}): "Vaporize",
    frozenset({"pyro", "cryo"}): "Melt",
    frozenset({"pyro", "electro"}): "Overloaded",
    frozenset({"cryo", "electro"}): "Superconduct",
    frozenset({"hydro", "electro"}): "Electro-Charged",
    frozenset({"cryo", "hydro"}): "Frozen",
    frozenset({"dendro", "hydro"}): "Bloom",
    frozenset({"dendro", "pyro"}): "Burning",
    frozenset({"dendro", "electro"}): "Quicken",
}

SWIRLABLE: set[str] = {"pyro", "hydro", "electro", "cryo"}
CRYSTALLIZABLE: set[str] = {"pyro", "hydro", "electro", "cryo"}


@dataclass
class CombatResult:
    ok: bool
    message: str = ""
    combat_action: bool = False
    ended_round: bool = False
    need_active: BattlePlayer | None = None
    winner: BattlePlayer | None = None
    reaction: str = ""
    logs: list[str] = field(default_factory=list)


class CombatEngine:
    def __init__(self, player: BattlePlayer, opponent: BattlePlayer) -> None:
        self.player: BattlePlayer = player
        self.opponent: BattlePlayer = opponent

    def other(self, user: BattlePlayer) -> BattlePlayer:
        return self.opponent if user is self.player else self.player

    def winner(self) -> BattlePlayer | None:
        player_down: bool = self.player.is_defeated()
        opponent_down: bool = self.opponent.is_defeated()
        if player_down and opponent_down:
            return None
        if opponent_down:
            return self.player
        if player_down:
            return self.opponent
        return None

    def _result(self, user: BattlePlayer, message: str, combat_action: bool = False, reaction: str = "", logs: list[str] | None = None) -> CombatResult:
        need_active: BattlePlayer | None = None
        for side in (user, self.other(user=user)):
            active: CharacterCard | None = side.active_character
            if active is None or not active.is_alive:
                alive: list[int] = side.alive_indexes()
                if alive:
                    need_active = side
                    break
        return CombatResult(
            ok=True,
            message=message,
            combat_action=combat_action,
            need_active=need_active,
            winner=self.winner(),
            reaction=reaction,
            logs=logs or [message],
        )

    def _fail(self, message: str) -> CombatResult:
        return CombatResult(ok=False, message=message)

    def skill_reductions(self, user: BattlePlayer, skill_key: SkillKey) -> dict[str, int]:
        character: CharacterCard | None = user.active_character
        reductions: dict[str, int] = {}
        if character is None:
            return reductions
        if skill_key == "normal" and character.minty_uses_left > 0:
            reductions["unaligned"] = 1
        artifact: ActionCard | None = character.artifact_card
        if artifact is None or character.artifact_used_this_round or skill_key == "normal":
            return reductions
        effect = artifact.effect
        if effect.get("condition") == "on_skill_use" and effect.get("element_target") == character.element:
            reductions[character.element] = int(effect.get("cost_reduction", 0))
        return reductions

    def can_use_skill(self, user: BattlePlayer, skill_key: SkillKey) -> tuple[bool, str]:
        character: CharacterCard | None = user.active_character
        if character is None or not character.is_alive:
            return False, "No active character"
        if character.frozen:
            return False, f"{character.name} is Frozen"
        skill: SkillModel | None = character.skills.get(skill_key)
        if skill is None:
            return False, "That skill does not exist"
        energy_cost: int = int(skill.get("cost", {}).get("energy", 0))
        if character.current_energy < energy_cost:
            return False, f"{character.name} needs {energy_cost} Energy"
        if user.choose_payment(cost=skill.get("cost", {}), reductions=self.skill_reductions(user=user, skill_key=skill_key)) is None:
            return False, "Not enough dice"
        return True, ""

    def use_skill(self, user: BattlePlayer, skill_key: SkillKey) -> CombatResult:
        ready, reason = self.can_use_skill(user=user, skill_key=skill_key)
        if not ready:
            return self._fail(reason)
        attacker: CharacterCard = user.active_character  # type: ignore[assignment]
        defender_side: BattlePlayer = self.other(user=user)
        defender: CharacterCard | None = defender_side.active_character
        if defender is None or not defender.is_alive:
            return self._fail("There is no one to attack")

        skill: SkillModel = attacker.skills[skill_key]
        reductions: dict[str, int] = self.skill_reductions(user=user, skill_key=skill_key)
        if not user.try_pay(cost=skill.get("cost", {}), reductions=reductions):
            return self._fail("Not enough dice")

        if reductions.get("unaligned") and skill_key == "normal" and attacker.minty_uses_left > 0:
            attacker.minty_uses_left -= 1
        if reductions.get(attacker.element) and attacker.artifact_card is not None:
            attacker.artifact_used_this_round = True

        energy_cost: int = int(skill.get("cost", {}).get("energy", 0))
        attacker.current_energy -= energy_cost

        logs: list[str] = [f"{attacker.name} used {skill.get('name', skill_key)}"]
        bonus: int = attacker.next_attack_bonus
        if attacker.weapon_card is not None:
            bonus += int(attacker.weapon_card.effect.get("damage", 0))
        attacker.next_attack_bonus = 0

        damage: int = int(skill.get("damage", 0)) + bonus
        incoming: ElementalTypes | None = skill.get("apply")
        reaction_name: str = ""
        if incoming:
            extra, reaction_name, reaction_logs = self._apply_element(target=defender, incoming=incoming, owner=defender_side)
            damage += extra
            logs.extend(reaction_logs)

        dealt: int = self._deal_damage(target=defender, amount=damage)
        if dealt:
            logs.append(f"{defender.name} took {dealt} damage")

        piercing: int = int(skill.get("piercing_damage", 0))
        if piercing:
            for character in defender_side.list_of_characters:
                if character.is_alive:
                    character.current_hp = max(0, character.current_hp - piercing)
            logs.append(f"{piercing} piercing damage to the enemy team")

        if skill.get("heal_team"):
            healed: int = 0
            for character in user.list_of_characters:
                healed += character.heal(amount=int(skill["heal_team"]))
            if healed:
                logs.append(f"Healed the team for {healed}")

        if skill.get("shield"):
            attacker.shield += int(skill["shield"])
            logs.append(f"{attacker.name} gained {skill['shield']} Shield")

        if skill.get("summon"):
            self._create_summon(user=user, name=str(skill["summon"]))
            logs.append(f"Summoned {skill['summon']}")

        if skill.get("force_swap"):
            swapped: str | None = self._force_swap(side=defender_side)
            if swapped:
                logs.append(f"{swapped} was swapped in")

        if skill.get("energy"):
            attacker.current_energy = min(attacker.max_energy, attacker.current_energy + int(skill["energy"]))

        if skill_key == "burst" and attacker.artifact_card is not None:
            artifact: ActionCard = attacker.artifact_card
            if artifact.effect.get("condition") == "on_burst_use" and not attacker.artifact_used_this_round:
                attacker.current_energy = min(attacker.max_energy, attacker.current_energy + int(artifact.effect.get("energy_gain", 0)))
                attacker.artifact_used_this_round = True
                logs.append(f"{artifact.name} restored Energy")

        self._clear_fallen(side=defender_side)
        self._clear_fallen(side=user)
        return self._result(user=user, message=logs[-1] if logs else attacker.name, combat_action=True, reaction=reaction_name, logs=logs)

    def _deal_damage(self, target: CharacterCard, amount: int) -> int:
        if amount <= 0 or not target.is_alive:
            return 0
        if target.frozen:
            amount += 2
            target.frozen = False
        blocked: int = min(target.shield, amount)
        target.shield -= blocked
        leftover: int = amount - blocked
        target.current_hp = max(0, target.current_hp - leftover)
        return leftover

    def _apply_element(self, target: CharacterCard, incoming: ElementalTypes, owner: BattlePlayer) -> tuple[int, str, list[str]]:
        if incoming == "omni" or not target.is_alive:
            return 0, "", []
        aura: ElementalTypes | None = target.applied_element
        if aura is None or aura == incoming:
            target.applied_element = incoming
            return 0, "", [f"{incoming.title()} applied to {target.name}"]

        pair: frozenset[str] = frozenset({aura, incoming})
        extra: int = 0
        name: str = ""
        logs: list[str] = []

        if incoming == "anemo" and aura in SWIRLABLE:
            name, extra = "Swirl", 1
            target.applied_element = None
            self._spread_element(side=owner, incoming=aura, skip=target)
            logs.append(f"Swirl spread {aura.title()}")
        elif aura == "anemo" and incoming in SWIRLABLE:
            name, extra = "Swirl", 1
            target.applied_element = None
            self._spread_element(side=owner, incoming=incoming, skip=target)
            logs.append(f"Swirl spread {incoming.title()}")
        elif incoming == "geo" and aura in CRYSTALLIZABLE:
            name, extra = "Crystallize", 1
            target.applied_element = None
            if owner.active_character:
                owner.active_character.shield += 1
        elif aura == "geo" and incoming in CRYSTALLIZABLE:
            name, extra = "Crystallize", 1
            target.applied_element = None
            if owner.active_character:
                owner.active_character.shield += 1
        elif pair in REACTION_NAMES:
            name = REACTION_NAMES[pair]
            extra = 2 if name in {"Vaporize", "Melt", "Overloaded"} else 1
            target.applied_element = None
            if name == "Frozen":
                target.frozen = True
                extra = 0
            if name in {"Superconduct", "Electro-Charged"}:
                extra = 0
                for character in owner.list_of_characters:
                    if character.is_alive:
                        character.current_hp = max(0, character.current_hp - 1)
                logs.append(f"{name} dealt 1 piercing to the team")
            if name == "Overloaded":
                swapped: str | None = self._force_swap(side=owner)
                if swapped:
                    logs.append(f"Overloaded swapped in {swapped}")
        else:
            target.applied_element = incoming
            return 0, "", [f"{incoming.title()} applied to {target.name}"]

        logs.insert(0, f"{name}!")
        return extra, name, logs

    def _spread_element(self, side: BattlePlayer, incoming: ElementalTypes, skip: CharacterCard) -> None:
        for character in side.list_of_characters:
            if character is skip or not character.is_alive:
                continue
            extra, _, _ = self._apply_element(target=character, incoming=incoming, owner=side)
            if extra:
                self._deal_damage(target=character, amount=extra)

    def _force_swap(self, side: BattlePlayer) -> str | None:
        active_index: int | None = side.active_character_index
        options: list[int] = [index for index in side.alive_indexes() if index != active_index]
        if not options:
            return None
        from random import choice
        side.set_active_character(index=choice(options))
        character: CharacterCard | None = side.active_character
        return character.name if character else None

    def _clear_fallen(self, side: BattlePlayer) -> None:
        for character in side.list_of_characters:
            if character.is_alive:
                continue
            character.current_hp = 0
            character.applied_element = None
            character.frozen = False
            character.shield = 0
        active: CharacterCard | None = side.active_character
        if active is not None and not active.is_alive:
            alive: list[int] = side.alive_indexes()
            if len(alive) == 1:
                side.active_character_index = alive[0]

    def _create_summon(self, user: BattlePlayer, name: str) -> None:
        existing: dict[str, object] | None = next((summon for summon in user.summons if summon["name"] == name), None)
        if name == "Baron Bunny":
            summon = {"name": name, "duration": 1, "damage": 2, "element": "pyro"}
        elif name == "Oz":
            summon = {"name": name, "duration": 2, "damage": 1, "element": "electro"}
        else:
            summon = {"name": name, "duration": 2, "damage": 1, "element": "cryo"}
        if existing is None:
            user.summons.append(summon)
        else:
            existing.update(summon)

    def card_needs_target(self, card: ActionCard) -> bool:
        effect = card.effect
        if effect.get("type") in {"location", "support"}:
            return False
        if effect.get("target") == "selected_character":
            return True
        if effect.get("restriction") or effect.get("condition") in {"next_attack", "on_burst_use", "on_skill_use"}:
            return True
        return effect.get("type") in {"food", "equipment"}

    def restriction_weapon(self, card: ActionCard) -> str | None:
        restriction: str | None = card.effect.get("restriction")
        if restriction is None:
            return None
        return WEAPON_RESTRICTIONS.get(restriction)

    def can_play_card(self, user: BattlePlayer, card: ActionCard, target_index: int | None) -> tuple[bool, str]:
        if user.choose_payment(cost=card.cost) is None:
            return False, "Not enough dice"
        effect = card.effect
        if effect.get("type") in {"location", "support"}:
            if user.has_support(card_id=card.card_id):
                return False, f"{card.name} is already in play"
            if len(user.supports) >= 4:
                return False, "Support zone is full"
            return True, ""

        if target_index is None:
            return False, "Choose a character"
        if not 0 <= target_index < len(user.list_of_characters):
            return False, "That character is not on the field"
        target: CharacterCard = user.list_of_characters[target_index]
        if not target.is_alive:
            return False, f"{target.name} has been defeated"

        needed_weapon: str | None = self.restriction_weapon(card=card)
        if needed_weapon and target.weapon != needed_weapon:
            return False, f"{card.name} can only be used by {needed_weapon} users"

        if effect.get("type") == "food":
            if target.satiated:
                return False, f"{target.name} already ate this round"
            if effect.get("heal") and target.current_hp >= target.max_hp and not effect.get("cost_reduction"):
                return False, f"{target.name} is already at full HP"
        return True, ""

    def play_card(self, user: BattlePlayer, hand_index: int, target_index: int | None) -> CombatResult:
        if not 0 <= hand_index < len(user.hand):
            return self._fail("That card is not in hand")
        card: ActionCard = user.hand[hand_index]
        ready, reason = self.can_play_card(user=user, card=card, target_index=target_index)
        if not ready:
            return self._fail(reason)
        if not user.try_pay(cost=card.cost):
            return self._fail("Not enough dice")

        del user.hand[hand_index]
        effect = card.effect
        logs: list[str] = [f"Played {card.name}"]

        if effect.get("type") in {"location", "support"}:
            user.supports.append(card)
            logs.append(f"{card.name} entered the support zone")
            return self._result(user=user, message=logs[-1], logs=logs)

        target: CharacterCard = user.list_of_characters[target_index]  # type: ignore[index]
        if self.restriction_weapon(card=card) is not None:
            target.weapon_card = card
            logs.append(f"{card.name} equipped on {target.name}")
        elif effect.get("condition") == "next_attack":
            target.next_attack_bonus += int(effect.get("damage", 0))
            logs.append(f"{card.name} empowered {target.name}")
        elif effect.get("condition") in {"on_burst_use", "on_skill_use"}:
            target.artifact_card = card
            logs.append(f"{card.name} equipped on {target.name}")
        elif effect.get("type") == "food":
            target.satiated = True
            healed: int = target.heal(amount=int(effect.get("heal", 0)))
            if healed:
                logs.append(f"{target.name} healed {healed}")
            if effect.get("target_action") == "normal_attack":
                target.minty_uses_left = int(effect.get("limit", 0) or 0)
                logs.append(f"{target.name}'s Normal Attacks cost less")
        else:
            target.next_attack_bonus += int(effect.get("damage", 0))
            logs.append(f"{card.name} used on {target.name}")

        return self._result(user=user, message=logs[-1], logs=logs)

    def can_switch(self, user: BattlePlayer, index: int, free: bool = False) -> tuple[bool, str]:
        if not 0 <= index < len(user.list_of_characters):
            return False, "That character is not on the field"
        if index == user.active_character_index:
            return False, "That character is already active"
        if not user.list_of_characters[index].is_alive:
            return False, "That character has been defeated"
        if free:
            return True, ""
        cost: int = max(0, SWITCH_COST - user.switch_discount())
        if cost and user.choose_payment(cost={"unaligned": cost}) is None:
            return False, "Not enough dice to switch"
        return True, ""

    def switch_character(self, user: BattlePlayer, index: int, free: bool = False) -> CombatResult:
        ready, reason = self.can_switch(user=user, index=index, free=free)
        if not ready:
            return self._fail(reason)
        cost: int = 0 if free else max(0, SWITCH_COST - user.switch_discount())
        if cost:
            if not user.try_pay(cost={"unaligned": cost}):
                return self._fail("Not enough dice to switch")
            if user.switch_discount():
                user.winery_used_this_round = True
        user.set_active_character(index=index)
        character: CharacterCard = user.list_of_characters[index]
        return self._result(user=user, message=f"Switched to {character.name}", combat_action=not free)

    def start_action_phase(self) -> list[str]:
        logs: list[str] = []
        for side in (self.player, self.opponent):
            for card in list(side.supports):
                if card.effect.get("phase") != "action_phase_start":
                    continue
                generated: dict[str, int] = card.effect.get("generate_dice", {})
                faces: list[ElementalTypes] = []
                for face, amount in generated.items():
                    faces.extend([face] * int(amount))  # type: ignore[arg-type]
                if faces:
                    side.add_dice(faces=faces)
                    logs.append(f"{card.name} created {len(faces)} dice")
                if card.duration_left:
                    card.duration_left -= 1
                    if card.duration_left <= 0:
                        side.supports.remove(card)
        return logs

    def end_phase(self) -> CombatResult:
        logs: list[str] = []
        for side in (self.player, self.opponent):
            enemy: BattlePlayer = self.other(user=side)
            for summon in list(side.summons):
                target: CharacterCard | None = enemy.active_character
                damage: int = int(summon.get("damage", 0))
                element: ElementalTypes | None = summon.get("element")  # type: ignore[assignment]
                if target and target.is_alive and damage:
                    extra: int = 0
                    reaction: str = ""
                    if element:
                        extra, reaction, reaction_logs = self._apply_element(target=target, incoming=element, owner=enemy)
                        logs.extend(reaction_logs)
                    dealt: int = self._deal_damage(target=target, amount=damage + extra)
                    logs.append(f"{summon['name']} dealt {dealt}" + (f" ({reaction})" if reaction else ""))
                summon["duration"] = int(summon.get("duration", 1)) - 1
                if int(summon["duration"]) <= 0:
                    side.summons.remove(summon)

            for card in side.supports:
                if card.effect.get("phase") == "end_phase" and card.effect.get("heal"):
                    active: CharacterCard | None = side.active_character
                    if active and active.is_alive:
                        healed: int = active.heal(amount=int(card.effect["heal"]))
                        if healed:
                            logs.append(f"{card.name} healed {active.name} for {healed}")

            self._clear_fallen(side=side)
            side.reset_round_flags()

        message: str = logs[-1] if logs else "End Phase"
        return CombatResult(ok=True, message=message, winner=self.winner(), logs=logs or [message])

    def auto_target(self, user: BattlePlayer, card: ActionCard) -> int | None:
        if not self.card_needs_target(card=card):
            return None
        needed_weapon: str | None = self.restriction_weapon(card=card)
        best: tuple[int, int] | None = None
        for index, character in enumerate(user.list_of_characters):
            if not character.is_alive:
                continue
            if needed_weapon and character.weapon != needed_weapon:
                continue
            if card.effect.get("type") == "food" and card.effect.get("heal") and character.current_hp >= character.max_hp:
                continue
            if card.effect.get("type") == "food" and character.satiated:
                continue
            score: int = character.max_hp - character.current_hp
            if index == user.active_character_index:
                score += 1
            if best is None or score > best[0]:
                best = (score, index)
        return None if best is None else best[1]

    def decide_bot_action(self, bot: BattlePlayer) -> tuple[str, SkillKey | None, int | None, int | None]:
        """Returns (kind, skill_key, hand_index, target_index). kind is skill, card, switch, or end."""
        for index, card in enumerate(bot.hand):
            target: int | None = self.auto_target(user=bot, card=card)
            if not self.can_play_card(user=bot, card=card, target_index=target)[0]:
                continue
            if self._card_is_worth_playing(user=bot, card=card, target_index=target):
                return "card", None, index, target

        for skill_key in ("burst", "skill", "normal"):
            if self.can_use_skill(user=bot, skill_key=skill_key)[0]:
                return "skill", skill_key, None, None

        active: CharacterCard | None = bot.active_character
        if active is not None and active.current_hp <= 3:
            safer: list[int] = [
                index for index in bot.alive_indexes()
                if index != bot.active_character_index and bot.list_of_characters[index].current_hp > active.current_hp
            ]
            if safer and self.can_switch(user=bot, index=safer[0])[0]:
                return "switch", None, None, safer[0]
        return "end", None, None, None

    def _card_is_worth_playing(self, user: BattlePlayer, card: ActionCard, target_index: int | None) -> bool:
        effect = card.effect
        if effect.get("type") in {"location", "support"}:
            return True
        if target_index is None:
            return False
        target: CharacterCard = user.list_of_characters[target_index]
        if effect.get("restriction") and target.weapon_card is not None:
            return False
        if effect.get("condition") in {"on_burst_use", "on_skill_use"} and target.artifact_card is not None:
            return False
        if effect.get("type") == "food" and effect.get("heal") and target.current_hp >= target.max_hp:
            return False
        return True
