

from typing import TypeAlias, Literal, TypedDict

from pygame import Surface

ElementalTypes: TypeAlias = Literal["anemo", "pyro", "hydro", "geo", "electro"]
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
    }
}

ACTION_DB = dict[str, list[str]]

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