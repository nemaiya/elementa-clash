from collections.abc import Mapping, Sequence
from itertools import combinations

from util.Game.engine.types import ALIGNED_ELEMENTS, CostKey, Element


def dice_cost_total(cost: Mapping[CostKey, int]) -> int:
    total = 0
    for key, amount in cost.items():
        if key != "energy":
            total += amount
    return total


def _pay_elemental(
    pool: list[Element],
    element: Element,
    needed: int,
) -> bool:
    if needed <= 0:
        return True
    taken = 0
    remaining: list[Element] = []
    for die in pool:
        if taken < needed and die == element:
            taken += 1
        else:
            remaining.append(die)
    pool[:] = remaining
    still = needed - taken
    if still <= 0:
        return True
    omni_left: list[Element] = []
    for die in pool:
        if still > 0 and die == "omni":
            still -= 1
        else:
            omni_left.append(die)
    pool[:] = omni_left
    return still == 0


def _can_pay_matching(pool: Sequence[Element], needed: int) -> bool:
    if needed <= 0:
        return True
    if len(pool) < needed:
        return False
    omni = sum(1 for d in pool if d == "omni")
    counts: dict[Element, int] = {}
    for die in pool:
        if die != "omni":
            counts[die] = counts.get(die, 0) + 1
    for aligned in ALIGNED_ELEMENTS:
        if counts.get(aligned, 0) + omni >= needed:
            return True
    return omni >= needed


def combo_pays(
    dice: Sequence[Element],
    indices: Sequence[int],
    cost: Mapping[CostKey, int],
) -> bool:
    pool = [dice[i] for i in indices]
    elemental_needs: list[tuple[Element, int]] = []
    unaligned = 0
    matching = 0
    for key, amount in cost.items():
        if amount <= 0 or key == "energy":
            continue
        if key == "unaligned":
            unaligned += amount
        elif key == "matching":
            matching += amount
        else:
            elemental_needs.append((key, amount))

    for element, needed in elemental_needs:
        if not _pay_elemental(pool, element, needed):
            return False

    if matching > 0:
        if not _can_pay_matching(pool, matching):
            return False
        # Spend matching as a same-element group, preferring the densest aligned face.
        omni = sum(1 for d in pool if d == "omni")
        best: Element | None = None
        best_count = -1
        for aligned in ALIGNED_ELEMENTS:
            n = sum(1 for d in pool if d == aligned)
            if n > best_count:
                best = aligned
                best_count = n
        spend_type: Element = best if best is not None and best_count + omni >= matching else "omni"
        spent = 0
        kept: list[Element] = []
        for die in pool:
            if spent < matching and (die == spend_type or die == "omni"):
                spent += 1
            else:
                kept.append(die)
        pool = kept
        if spent < matching:
            return False

    return len(pool) >= unaligned


def find_dice_payment(
    dice: Sequence[Element],
    cost: Mapping[CostKey, int],
) -> list[int] | None:
    needed = dice_cost_total(cost)
    if needed == 0:
        return []
    if needed > len(dice):
        return None
    for combo in combinations(range(len(dice)), needed):
        if combo_pays(dice, combo, cost):
            return list(combo)
    return None
