from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from util.Game.engine.catalog import ActionCardDef, CharacterDef, SkillDef, SummonDef
from util.Game.engine.types import CardKind, Element, PlayerId, SkillKind, WeaponType


def new_id() -> str:
    return uuid4().hex[:10]


@dataclass
class ActionCardState:
    instance_id: str
    defn: ActionCardDef
    remaining_rounds: int = 0
    once_per_round_used: bool = False

    @property
    def name(self) -> str:
        return self.defn.name

    @property
    def kind(self) -> CardKind:
        return self.defn.kind

    @classmethod
    def from_def(cls, defn: ActionCardDef) -> ActionCardState:
        return cls(instance_id=new_id(), defn=defn, remaining_rounds=defn.duration_rounds)


@dataclass
class SummonState:
    instance_id: str
    defn: SummonDef
    usages: int

    @property
    def name(self) -> str:
        return self.defn.name

    @classmethod
    def from_def(cls, defn: SummonDef) -> SummonState:
        return cls(instance_id=new_id(), defn=defn, usages=defn.usages)


@dataclass
class CharacterState:
    defn: CharacterDef
    hp: int
    energy: int
    shield: int = 0
    equipment: ActionCardState | None = None
    applied_element: Element | None = None
    food_used_this_round: bool = False

    @property
    def name(self) -> str:
        return self.defn.name

    @property
    def element(self) -> Element:
        return self.defn.element

    @property
    def weapon(self) -> WeaponType:
        return self.defn.weapon

    @property
    def max_hp(self) -> int:
        return self.defn.max_hp

    @property
    def max_energy(self) -> int:
        return self.defn.max_energy

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def skill(self, kind: SkillKind) -> SkillDef:
        return self.defn.skills[kind]

    @classmethod
    def from_def(cls, defn: CharacterDef) -> CharacterState:
        return cls(defn=defn, hp=defn.max_hp, energy=0)


@dataclass
class PlayerState:
    player_id: PlayerId
    name: str
    characters: list[CharacterState]
    deck: list[ActionCardState]
    hand: list[ActionCardState]
    supports: list[ActionCardState]
    summons: list[SummonState]
    dice: list[Element]
    active_index: int | None = None
    ended_round: bool = False
    mulligan_done: bool = False
    reroll_done: bool = False
    active_selected: bool = False
    switch_discount_used: bool = False

    def active(self) -> CharacterState | None:
        if self.active_index is None:
            return None
        return self.characters[self.active_index]

    def alive_indices(self) -> list[int]:
        return [i for i, c in enumerate(self.characters) if c.alive]

    def alive_standby_indices(self) -> list[int]:
        return [i for i in self.alive_indices() if i != self.active_index]

    def has_living_character(self) -> bool:
        return len(self.alive_indices()) > 0

    def reset_round_flags(self) -> None:
        self.ended_round = False
        self.reroll_done = False
        self.switch_discount_used = False
        for c in self.characters:
            c.food_used_this_round = False
            if c.equipment is not None:
                c.equipment.once_per_round_used = False
        for s in self.supports:
            s.once_per_round_used = False
