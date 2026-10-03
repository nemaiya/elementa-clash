from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from util.Game.engine.types import PlayerId, SkillKind

JsonObject: TypeAlias = dict[str, object]


@dataclass(frozen=True)
class ConfirmMulligan:
    player_id: PlayerId
    discard_instance_ids: tuple[str, ...]
    kind: Literal["confirm_mulligan"] = "confirm_mulligan"


@dataclass(frozen=True)
class SelectActive:
    player_id: PlayerId
    character_index: int
    kind: Literal["select_active"] = "select_active"


@dataclass(frozen=True)
class ConfirmReroll:
    player_id: PlayerId
    die_indices: tuple[int, ...]
    kind: Literal["confirm_reroll"] = "confirm_reroll"


@dataclass(frozen=True)
class UseSkill:
    player_id: PlayerId
    skill: SkillKind
    die_indices: tuple[int, ...]
    kind: Literal["use_skill"] = "use_skill"


@dataclass(frozen=True)
class SwitchCharacter:
    player_id: PlayerId
    character_index: int
    die_indices: tuple[int, ...]
    kind: Literal["switch_character"] = "switch_character"


@dataclass(frozen=True)
class EndRound:
    player_id: PlayerId
    kind: Literal["end_round"] = "end_round"


@dataclass(frozen=True)
class PlayActionCard:
    player_id: PlayerId
    card_instance_id: str
    die_indices: tuple[int, ...]
    target_character_index: int | None = None
    kind: Literal["play_action_card"] = "play_action_card"


@dataclass(frozen=True)
class ElementalTuning:
    player_id: PlayerId
    card_instance_id: str
    die_index: int
    kind: Literal["elemental_tuning"] = "elemental_tuning"


@dataclass(frozen=True)
class ForcedSwitch:
    player_id: PlayerId
    character_index: int
    kind: Literal["forced_switch"] = "forced_switch"


Action: TypeAlias = (
    ConfirmMulligan
    | SelectActive
    | ConfirmReroll
    | UseSkill
    | SwitchCharacter
    | EndRound
    | PlayActionCard
    | ElementalTuning
    | ForcedSwitch
)


def action_to_json(action: Action) -> JsonObject:
    data: JsonObject = {"type": action.kind, "player_id": action.player_id}
    if isinstance(action, ConfirmMulligan):
        data["discard_instance_ids"] = list(action.discard_instance_ids)
    elif isinstance(action, SelectActive):
        data["character_index"] = action.character_index
    elif isinstance(action, ConfirmReroll):
        data["die_indices"] = list(action.die_indices)
    elif isinstance(action, UseSkill):
        data["skill"] = action.skill
        data["die_indices"] = list(action.die_indices)
    elif isinstance(action, SwitchCharacter):
        data["character_index"] = action.character_index
        data["die_indices"] = list(action.die_indices)
    elif isinstance(action, PlayActionCard):
        data["card_instance_id"] = action.card_instance_id
        data["die_indices"] = list(action.die_indices)
        data["target_character_index"] = action.target_character_index
    elif isinstance(action, ElementalTuning):
        data["card_instance_id"] = action.card_instance_id
        data["die_index"] = action.die_index
    elif isinstance(action, ForcedSwitch):
        data["character_index"] = action.character_index
    return data


def _as_int(value: object) -> int:
    if not isinstance(value, int):
        raise ValueError("expected int")
    return value


def _as_str(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("expected str")
    return value


def _as_player_id(value: object) -> PlayerId:
    n = _as_int(value)
    if n not in (0, 1):
        raise ValueError("player_id must be 0 or 1")
    return 0 if n == 0 else 1


def _as_int_tuple(value: object) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise ValueError("expected list")
    return tuple(_as_int(item) for item in value)


def _as_str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("expected list")
    return tuple(_as_str(item) for item in value)


def action_from_json(data: JsonObject) -> Action:
    kind = _as_str(data.get("type"))
    player_id = _as_player_id(data.get("player_id"))
    if kind == "confirm_mulligan":
        return ConfirmMulligan(player_id, _as_str_tuple(data.get("discard_instance_ids", [])))
    if kind == "select_active":
        return SelectActive(player_id, _as_int(data.get("character_index")))
    if kind == "confirm_reroll":
        return ConfirmReroll(player_id, _as_int_tuple(data.get("die_indices", [])))
    if kind == "use_skill":
        skill = _as_str(data.get("skill"))
        if skill not in ("normal", "skill", "burst"):
            raise ValueError("invalid skill")
        return UseSkill(player_id, skill, _as_int_tuple(data.get("die_indices", [])))
    if kind == "switch_character":
        return SwitchCharacter(
            player_id,
            _as_int(data.get("character_index")),
            _as_int_tuple(data.get("die_indices", [])),
        )
    if kind == "end_round":
        return EndRound(player_id)
    if kind == "play_action_card":
        target_raw = data.get("target_character_index")
        target: int | None
        if target_raw is None:
            target = None
        else:
            target = _as_int(target_raw)
        return PlayActionCard(
            player_id,
            _as_str(data.get("card_instance_id")),
            _as_int_tuple(data.get("die_indices", [])),
            target,
        )
    if kind == "elemental_tuning":
        return ElementalTuning(
            player_id,
            _as_str(data.get("card_instance_id")),
            _as_int(data.get("die_index")),
        )
    if kind == "forced_switch":
        return ForcedSwitch(player_id, _as_int(data.get("character_index")))
    raise ValueError(f"unknown action type: {kind}")
