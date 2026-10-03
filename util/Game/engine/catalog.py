from dataclasses import dataclass

from util.Game.engine.types import CardKind, CostKey, Element, SkillKind, WeaponType


@dataclass(frozen=True)
class SkillDef:
    name: str
    cost: dict[CostKey, int]
    damage: int = 0
    energy_gain: int = 0
    apply: Element | None = None
    force_swap: bool = False
    heal_team: int = 0
    summon_id: str | None = None
    shield: int = 0
    piercing_damage: int = 0


@dataclass(frozen=True)
class CharacterDef:
    card_id: str
    name: str
    element: Element
    weapon: WeaponType
    max_hp: int
    max_energy: int
    skills: dict[SkillKind, SkillDef]


@dataclass(frozen=True)
class ActionCardDef:
    card_id: str
    name: str
    kind: CardKind
    cost: dict[CostKey, int]
    description: str
    restriction: str | None = None
    heal: int = 0
    damage_bonus: int = 0
    generate_omni: int = 0
    duration_rounds: int = 0
    switch_cost_reduction: int = 0
    end_phase_heal_active: int = 0
    energy_on_burst: int = 0
    skill_cost_reduction_element: Element | None = None


@dataclass(frozen=True)
class SummonDef:
    summon_id: str
    name: str
    element: Element
    damage: int
    usages: int


CHARACTER_CATALOG: dict[str, CharacterDef] = {
    "jean": CharacterDef(
        card_id="jean",
        name="Jean",
        element="anemo",
        weapon="sword",
        max_hp=10,
        max_energy=3,
        skills={
            "normal": SkillDef("Favonius Bladework", {"anemo": 1, "unaligned": 2}, damage=2, energy_gain=1),
            "skill": SkillDef("Gale Blade", {"anemo": 3}, damage=3, energy_gain=1, apply="anemo", force_swap=True),
            "burst": SkillDef("Dandelion Breeze", {"anemo": 4, "energy": 3}, damage=2, heal_team=2),
        },
    ),
    "amber": CharacterDef(
        card_id="amber",
        name="Amber",
        element="pyro",
        weapon="bow",
        max_hp=10,
        max_energy=2,
        skills={
            "normal": SkillDef("Sharpshooter", {"pyro": 1, "unaligned": 2}, damage=2, energy_gain=1),
            "skill": SkillDef("Explosive Puppet", {"pyro": 3}, damage=0, energy_gain=1, summon_id="baron_bunny", shield=2),
            "burst": SkillDef("Fiery Rain", {"pyro": 3, "energy": 2}, damage=2, piercing_damage=2),
        },
    ),
    "fischl": CharacterDef(
        card_id="fischl",
        name="Fischl",
        element="electro",
        weapon="bow",
        max_hp=10,
        max_energy=3,
        skills={
            "normal": SkillDef("Bolts of Downfall", {"electro": 1, "unaligned": 2}, damage=2, energy_gain=1),
            "skill": SkillDef("Nightrider", {"electro": 3}, damage=1, energy_gain=1, summon_id="oz", apply="electro"),
            "burst": SkillDef("Midnight Phantasmagoria", {"electro": 3, "energy": 3}, damage=4, piercing_damage=2),
        },
    ),
    "kaeya": CharacterDef(
        card_id="kaeya",
        name="Kaeya",
        element="cryo",
        weapon="sword",
        max_hp=10,
        max_energy=2,
        skills={
            "normal": SkillDef("Ceremonial Bladework", {"cryo": 1, "unaligned": 2}, damage=2, energy_gain=1),
            "skill": SkillDef("Frostgnaw", {"cryo": 3}, damage=3, energy_gain=1, apply="cryo"),
            "burst": SkillDef("Glacial Waltz", {"cryo": 4, "energy": 2}, damage=1, apply="cryo", summon_id="icicle"),
        },
    ),
}

ACTION_CATALOG: dict[str, ActionCardDef] = {
    "magic_guide": ActionCardDef(
        "magic_guide", "Magic Guide", "equipment", {"unaligned": 1},
        "Attach: +1 skill damage. Catalyst only.", restriction="catalyst", damage_bonus=1,
    ),
    "raven_bow": ActionCardDef(
        "raven_bow", "Raven Bow", "equipment", {"unaligned": 1},
        "Attach: +1 skill damage. Bow only.", restriction="bow", damage_bonus=1,
    ),
    "travelers_handy_sword": ActionCardDef(
        "travelers_handy_sword", "Traveler's Handy Sword", "equipment", {"unaligned": 1},
        "Attach: +1 skill damage. Sword only.", restriction="sword", damage_bonus=1,
    ),
    "white_iron_greatsword": ActionCardDef(
        "white_iron_greatsword", "White Iron Greatsword", "equipment", {"unaligned": 1},
        "Attach: +1 skill damage. Claymore only.", restriction="claymore", damage_bonus=1,
    ),
    "exiles_circlet": ActionCardDef(
        "exiles_circlet", "Exile's Circlet", "equipment", {"unaligned": 2},
        "On Burst: gain 1 Energy (once per round).", energy_on_burst=1,
    ),
    "broken_rimes_echo": ActionCardDef(
        "broken_rimes_echo", "Broken Rime's Echo", "equipment", {"unaligned": 1},
        "Cryo skills cost 1 less Cryo (once per round).", skill_cost_reduction_element="cryo",
    ),
    "witchs_scorching_hat": ActionCardDef(
        "witchs_scorching_hat", "Witch's Scorching Hat", "equipment", {"unaligned": 1},
        "Pyro skills cost 1 less Pyro (once per round).", skill_cost_reduction_element="pyro",
    ),
    "dawn_winery": ActionCardDef(
        "dawn_winery", "Dawn Winery", "support", {"matching": 2},
        "Switch costs 1 less Die (once per round).", switch_cost_reduction=1,
    ),
    "favonious_cathedral": ActionCardDef(
        "favonious_cathedral", "Favonius Cathedral", "support", {"matching": 2},
        "End Phase: heal active character 2 HP.", end_phase_heal_active=2,
    ),
    "paimon": ActionCardDef(
        "paimon", "Paimon", "support", {"matching": 3},
        "Action Phase start: create 2 Omni. Lasts 2 rounds.",
        generate_omni=2, duration_rounds=2,
    ),
    "sweet_madame": ActionCardDef(
        "sweet_madame", "Sweet Madame", "event", {"unaligned": 0},
        "Heal target character 1 HP.", heal=1,
    ),
    "mondstadt_hash_brown": ActionCardDef(
        "mondstadt_hash_brown", "Mondstadt Hash Brown", "event", {"unaligned": 1},
        "Heal target character 2 HP.", heal=2,
    ),
}

SUMMON_CATALOG: dict[str, SummonDef] = {
    "baron_bunny": SummonDef("baron_bunny", "Baron Bunny", "pyro", damage=2, usages=1),
    "oz": SummonDef("oz", "Oz", "electro", damage=1, usages=2),
    "icicle": SummonDef("icicle", "Icicle", "cryo", damage=2, usages=2),
}

P1_CHARACTERS: tuple[str, str, str] = ("kaeya", "amber", "fischl")
P2_CHARACTERS: tuple[str, str, str] = ("jean", "amber", "kaeya")

TEST_ACTION_DECK: tuple[str, ...] = (
    "raven_bow",
    "travelers_handy_sword",
    "sweet_madame",
    "sweet_madame",
    "mondstadt_hash_brown",
    "dawn_winery",
    "favonious_cathedral",
    "paimon",
    "broken_rimes_echo",
    "witchs_scorching_hat",
)


def starting_action_ids() -> list[str]:
    return list(TEST_ACTION_DECK)
