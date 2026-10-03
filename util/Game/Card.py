

from typing import TypeAlias, Literal, TypedDict

from pygame import Surface

ElementalTypes: TypeAlias = Literal["anemo", "pyro", "hydro", "geo", "electro", "dendro", "cryo", "omni"]
WeaponTypes: TypeAlias = Literal["sword", "bow", "claymore"]
CostType: TypeAlias = ElementalTypes | Literal["unaligned", "energy"]

class SkillModel(TypedDict, total=False):
    name: str
    cost: dict[CostType, int]
    type: str
    damage: int
    energy: int
    apply: ElementalTypes
    force_swap: bool
    heal_team: int
    summon: str
    shield: int
    piercing_damage: int

class CharacterModel(TypedDict):
    name: str
    image_key: str
    element: ElementalTypes
    weapon: WeaponTypes
    max_hp: int
    max_energy: int
    skills: dict[Literal["normal" , "skill" , "burst"], SkillModel]



    
CHARACTER_DB: dict[str, CharacterModel] = {
    "jean": {
        "name": "Jean",
        "image_key": "jean", # Maps to AssetManager.images["jean"]
        "element": "anemo",
        "weapon": "sword",
        "max_hp": 10,
        "max_energy": 3,
        "skills": {
            "normal": {"name": "Favonius Bladework", "cost": {"anemo": 1, "unaligned": 2}, "damage": 2, "energy": 1},
            "skill": {"name": "Gale Blade", "cost": {"anemo": 3}, "damage": 3, "energy": 1, "apply": "anemo", "force_swap": True},
            "burst": {"name": "Dandelion Breeze", "cost": {"anemo": 4, "energy": 3}, "damage": 2, "heal_team": 2}
        }
    },
    "amber": {
        "name": "Amber",
        "image_key": "amber",
        "element": "pyro",
        "weapon": "bow",
        "max_hp": 10,
        "max_energy": 2,
        "skills": {
            "normal": {"name": "Sharpshooter", "cost": {"pyro": 1, "unaligned": 2}, "damage": 2, "energy": 1},
            "skill": {"name": "Explosive Puppet", "cost": {"pyro": 3}, "damage": 0, "energy": 1, "summon": "Baron Bunny", "shield": 2},
            "burst": {"name": "Fiery Rain", "cost": {"pyro": 3, "energy": 2}, "damage": 2, "piercing_damage": 2}
        }
    },
    "fischl": {
        "name": "Fischl", 
        "image_key": "fischl",
        "element": "electro",
        "weapon": "bow",
        "max_hp": 10, # Adjusted from 27 to the standard 10 HP for Genius Invokation TCG
        "max_energy": 3,
        "skills": {
            "normal": {"name": "Bolts of Downfall", "cost": {"electro": 1, "unaligned": 2}, "damage": 2, "energy": 1},
            "skill": {"name": "Nightrider", "cost": {"electro": 3}, "damage": 1, "energy": 1, "summon": "Oz", "apply": "electro"},
            "burst": {"name": "Midnight Phantasmagoria", "cost": {"electro": 3, "energy": 3}, "damage": 4, "piercing_damage": 2}
        }
    },
    "kaeya": {
        "name": "Kaeya",
        "image_key": "kaeya",
        "element": "cryo",
        "weapon": "sword",
        "max_hp": 10,
        "max_energy": 2,
        "skills": {
            "normal": {"name": "Ceremonial Bladework", "cost": {"cryo": 1, "unaligned": 2}, "damage": 2, "energy": 1},
            "skill": {"name": "Frostgnaw", "cost": {"cryo": 3}, "damage": 3, "energy": 1, "apply": "cryo"},
            "burst": {"name": "Glacial Waltz", "cost": {"cryo": 4, "energy": 2}, "damage": 1, "apply": "cryo", "summon": "icicle"}
        }
    }
}

ActionCostType: TypeAlias = ElementalTypes | Literal["unaligned", "matching", "energy"]
CardCategory: TypeAlias = Literal["equipment", "support", "event", "food", "location"]

class EffectModel(TypedDict, total=False):
    type: CardCategory
    damage: int
    heal: int
    condition: str
    restriction: str
    energy_gain: int
    limit: int | str
    cost_reduction: int
    switch_cost_reduction: int
    element_target: ElementalTypes
    target: str
    phase: str
    generate_dice: dict[str, int]
    duration: int | str
    target_action: str

class ActionCardModel(TypedDict):
    name: str
    image_key: str
    cost: dict[ActionCostType, int]
    effect_description: str
    effect: EffectModel

ACTION_DB: dict[str, ActionCardModel] = {
    "magic_guide": {
        "name": "Magic Guide",
        "image_key": "magic_guide",
        "cost": {"unaligned": 1},
        "effect_description": "The selected character deals +1 damage on their next attack. Only Catalyst users can use this card.",
        "effect": {"damage": 1, "condition": "next_attack", "restriction": "catalyst_user"}
    },
    "raven_bow": {
        "name": "Raven Bow",
        "image_key": "raven_bow",
        "cost": {"unaligned": 1},
        "effect_description": "The selected character deals +1 damage on their next attack. Only Bow users can use this card.",
        "effect": {"damage": 1, "condition": "next_attack", "restriction": "bow_user"}
    },
    "white_iron_greatsword": {
        "name": "White Iron Greatsword",
        "image_key": "white_iron_greatsword",
        "cost": {"unaligned": 1},
        "effect_description": "The selected character deals +1 damage on their next attack. Only Claymore users can use this card.",
        "effect": {"damage": 1, "condition": "next_attack", "restriction": "claymore_user"}
    },
    "white_tassel": {
        "name": "White Tassel",
        "image_key": "white_tassel",
        "cost": {"unaligned": 1},
        "effect_description": "The selected character deals +1 damage on their next attack. Only Polearm users can use this card.",
        "effect": {"damage": 1, "condition": "next_attack", "restriction": "polearm_user"}
    },
    "travelers_handy_sword": {
        "name": "Traveler's Handy Sword",
        "image_key": "travelers_handy_sword",
        "cost": {"unaligned": 1},
        "effect_description": "The selected character deals +1 damage on their next attack. Only Sword users can use this card.",
        "effect": {"damage": 1, "condition": "next_attack", "restriction": "sword_user"}
    },
    "exiles_circlet": {
        "name": "Exile's Circlet",
        "image_key": "exiles_circlet",
        "cost": {"unaligned": 2},
        "effect_description": "When the attached character uses an Elemental Burst, they gain 1 Energy. (Once per Round)",
        "effect": {"energy_gain": 1, "condition": "on_burst_use", "limit": "once_per_round"}
    },
    "broken_rimes_echo": {
        "name": "Broken Rime's Echo",
        "image_key": "broken_rimes_echo",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses a Cryo Skill, spend 1 less Cryo Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "cryo", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "wine_stained_tricorne": {
        "name": "Wine-Stained Tricorne",
        "image_key": "wine_stained_tricorne",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses a Hydro Skill, spend 1 less Hydro Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "hydro", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "witchs_scorching_hat": {
        "name": "Witch's Scorching Hat",
        "image_key": "witchs_scorching_hat",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses a Pyro Skill, spend 1 less Pyro Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "pyro", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "thunder_summoners_crown": {
        "name": "Thunder Summoner's Crown",
        "image_key": "thunder_summoners_crown",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses an Electro Skill, spend 1 less Electro Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "electro", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "viridescent_venerers_diadem": {
        "name": "Viridescent Venerer's Diadem",
        "image_key": "viridescent_venerers_diadem",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses an Anemo Skill, spend 1 less Anemo Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "anemo", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "mask_of_solitude_basalt": {
        "name": "Mask of Solitude Basalt",
        "image_key": "mask_of_solitude_basalt",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses a Geo Skill, spend 1 less Geo Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "geo", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "laurel_coronet": {
        "name": "Laurel Coronet",
        "image_key": "laurel_coronet",
        "cost": {"unaligned": 1},
        "effect_description": "When the attached character uses a Dendro Skill, spend 1 less Dendro Die. (Once per Round)",
        "effect": {"cost_reduction": 1, "element_target": "dendro", "condition": "on_skill_use", "limit": "once_per_round"}
    },
    "dawn_winery": {
        "name": "Dawn Winery",
        "image_key": "dawn_winery",
        "cost": {"matching": 2},
        "effect_description": "Location: When you perform \"Switch Character\", spend 1 less Elemental Die. (Once per Round)",
        "effect": {"switch_cost_reduction": 1, "type": "location", "limit": "once_per_round"}
    },
    "favonious_cathedral": {
        "name": "Favonious Cathedral",
        "image_key": "favonious_cathedral",
        "cost": {"matching": 2},
        "effect_description": "Location: End Phase: Heal your active character for 2 HP.",
        "effect": {"heal": 2, "target": "active_character", "type": "location", "phase": "end_phase"}
    },
    "paimon": {
        "name": "Paimon",
        "image_key": "paimon",
        "cost": {"matching": 3},
        "effect_description": "Support: Action Phase starts: Create 2 Omni Element Dice. Lasts for 2 Rounds.",
        "effect": {"generate_dice": {"omni": 2}, "type": "support", "phase": "action_phase_start", "duration": 2}
    },
    "sweet_madame": {
        "name": "Sweet Madame",
        "image_key": "sweet_madame",
        "cost": {"unaligned": 0},
        "effect_description": "Food: Heals the target character for 1 HP.",
        "effect": {"heal": 1, "target": "selected_character", "type": "food"}
    },
    "mondstadt_hash_brown": {
        "name": "Mondstadt Hash Brown",
        "image_key": "mondstadt_hash_brown",
        "cost": {"unaligned": 1},
        "effect_description": "Food: Heals the target character for 2 HP.",
        "effect": {"heal": 2, "target": "selected_character", "type": "food"}
    },
    "minty_meat_rolls": {
        "name": "Minty Meat Rolls",
        "image_key": "minty_meat_rolls",
        "cost": {"unaligned": 1},
        "effect_description": "Food: Before the target character uses a Normal Attack this round, spend 1 less Unaligned Die. (Max 3 times)",
        "effect": {"cost_reduction": 1, "target_action": "normal_attack", "type": "food", "limit": 3, "duration": "current_round"}
    }
}

class Card:
    def __init__(self, name: str, image_key: str) -> None:
        self.name: str = name
        self.image_key: str = image_key


class CharacterCard(Card):
    def __init__(self, character_id: str) -> None:
        # Fetch data from the DB using the character ID (e.g., "jean", "amber")
        data = CHARACTER_DB.get(character_id)
        if not data:
            raise ValueError(f"Character '{character_id}' not found in CHARACTER_DB.")

        # Initialize base card properties
        super().__init__(name=data["name"], image_key=data["image_key"])

        # Set character-specific combat stats
        self.element: ElementalTypes = data["element"]
        self.weapon: WeaponTypes = data["weapon"]
        self.max_hp: int = data["max_hp"]
        self.current_hp: int = data["max_hp"]  # Starts at max HP
        self.max_energy: int = data["max_energy"]
        self.current_energy: int = 0           # Starts at 0 energy
        self.skills: dict[Literal["normal", "skill", "burst"], SkillModel] = data["skills"]


class ActionCard(Card):
    def __init__(self, name: str, image_key: str, cost: dict[CostType, int], effect_description: str) -> None:
        super().__init__(name, image_key)
        self.cost: dict[CostType, int] = cost
        self.effect_description: str = effect_description