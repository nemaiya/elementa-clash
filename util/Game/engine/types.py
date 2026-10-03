from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, TypeAlias

Element: TypeAlias = Literal[
    "pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo", "omni"
]
WeaponType: TypeAlias = Literal["sword", "bow", "claymore", "polearm", "catalyst"]
SkillKind: TypeAlias = Literal["normal", "skill", "burst"]
CardKind: TypeAlias = Literal["equipment", "support", "event"]
CostKey: TypeAlias = Element | Literal["unaligned", "matching", "energy"]
PlayerId: TypeAlias = Literal[0, 1]

ELEMENTS: tuple[Element, ...] = (
    "pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo", "omni"
)
DICE_FACES: tuple[Element, ...] = ELEMENTS
ALIGNED_ELEMENTS: tuple[Element, ...] = (
    "pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo"
)

ELEMENT_COLORS: dict[Element, tuple[int, int, int]] = {
    "pyro": (210, 62, 42),
    "hydro": (42, 108, 214),
    "anemo": (64, 196, 168),
    "electro": (148, 78, 214),
    "dendro": (78, 168, 52),
    "cryo": (96, 198, 228),
    "geo": (214, 176, 52),
    "omni": (236, 236, 236),
}


class Phase(Enum):
    MULLIGAN = "mulligan"
    SELECT_ACTIVE = "select_active"
    ROLL = "roll"
    REROLL = "reroll"
    ACTION = "action"
    FORCED_SWITCH = "forced_switch"
    END_PHASE = "end_phase"
    GAME_OVER = "game_over"


class HitKind(Enum):
    HAND = "hand"
    CHARACTER = "character"
    DIE = "die"
    SKILL = "skill"
    CONFIRM = "confirm"
    END_ROUND = "end_round"
    TUNE = "tune"
    OPPONENT_CHARACTER = "opponent_character"


@dataclass(frozen=True)
class HitTarget:
    kind: HitKind
    index: int = 0
    instance_id: str = ""
    skill: SkillKind | None = None
    player_id: PlayerId = 0


@dataclass
class HitRegion:
    x: int
    y: int
    width: int
    height: int
    target: HitTarget

    def contains(self, pos: tuple[int, int]) -> bool:
        px, py = pos
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height


@dataclass
class UiSelection:
    hand_ids: set[str] = field(default_factory=set)
    die_indices: set[int] = field(default_factory=set)
    character_index: int | None = None
