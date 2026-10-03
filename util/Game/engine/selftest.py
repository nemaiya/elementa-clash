from __future__ import annotations

from random import Random

from util.Game.engine.actions import (
    ConfirmMulligan,
    ConfirmReroll,
    ElementalTuning,
    EndRound,
    ForcedSwitch,
    PlayActionCard,
    SelectActive,
    SwitchCharacter,
    UseSkill,
    action_from_json,
    action_to_json,
)
from util.Game.engine.catalog import ACTION_CATALOG, SUMMON_CATALOG
from util.Game.engine.entities import ActionCardState, SummonState
from util.Game.engine.game_model import HAND_LIMIT, ZONE_LIMIT, GameModel
from util.Game.engine.types import Phase


def _open_action(model: GameModel) -> GameModel:
    assert model.phase == Phase.MULLIGAN
    assert all(len(p.hand) == 5 for p in model.players)
    assert all(len(p.deck) == 5 for p in model.players)
    assert model.apply(ConfirmMulligan(0, ()))
    assert model.apply(ConfirmMulligan(1, ()))
    assert model.phase == Phase.SELECT_ACTIVE
    assert model.apply(SelectActive(0, 0))
    assert model.apply(SelectActive(1, 0))
    assert model.phase == Phase.REROLL
    assert all(len(p.dice) == 8 for p in model.players)
    assert model.apply(ConfirmReroll(0, ()))
    assert model.apply(ConfirmReroll(1, ()))
    assert model.phase == Phase.ACTION
    return model


def test_mulligan_replaces_once() -> None:
    model = GameModel(rng=Random(1))
    original = [c.instance_id for c in model.player(0).hand]
    discard = tuple(original[:2])
    assert model.apply(ConfirmMulligan(0, discard))
    kept = {c.instance_id for c in model.player(0).hand}
    assert discard[0] not in kept and discard[1] not in kept
    assert len(model.player(0).hand) == 5
    assert model.validate(ConfirmMulligan(0, ())) == "not this player's window"


def test_phase_gate_and_fast_vs_combat() -> None:
    model = _open_action(GameModel(rng=Random(2)))
    assert model.current_player == 0
    p0 = model.player(0)
    p0.dice = ["omni"] * 8
    model.player(1).dice = ["omni"] * 8
    skill = UseSkill(0, "normal", (0, 1, 2))
    assert model.apply(skill)
    assert model.current_player == 1
    model.player(1).dice = ["omni"] * 8
    food = next(c for c in model.player(1).hand if c.defn.heal > 0)
    before_turn = model.current_player
    pay = model.suggest_payment(1, dict(food.defn.cost))
    assert pay is not None or sum(v for k, v in food.defn.cost.items() if k != "energy") == 0
    assert model.apply(
        PlayActionCard(1, food.instance_id, tuple(pay or []), model.player(1).active_index)
    )
    assert model.current_player == before_turn
    assert model.phase == Phase.ACTION


def test_end_round_first_player_next_round() -> None:
    model = _open_action(GameModel(rng=Random(3)))
    assert model.apply(EndRound(0))
    assert model.first_ender == 0
    assert model.current_player == 1
    assert model.apply(EndRound(1))
    assert model.phase == Phase.REROLL
    assert model.round_number == 2
    assert model.apply(ConfirmReroll(0, ()))
    assert model.apply(ConfirmReroll(1, ()))
    assert model.current_player == 0


def test_forced_switch_and_empty_deck() -> None:
    model = _open_action(GameModel(rng=Random(4)))
    victim = model.player(1)
    victim.characters[0].hp = 1
    model.player(0).dice = ["omni"] * 8
    assert model.apply(UseSkill(0, "normal", (0, 1, 2)))
    assert model.phase == Phase.FORCED_SWITCH
    assert model.forced_switch_player == 1
    assert model.validate(EndRound(1)) == "must force-switch the fallen active character"
    assert model.apply(ForcedSwitch(1, 1))
    assert model.phase == Phase.ACTION
    assert model.player(1).active_index == 1
    model.player(1).deck.clear()
    before = len(model.player(1).hand)
    model._draw_cards(model.player(1), 2)
    assert len(model.player(1).hand) == before


def test_zone_and_hand_limits() -> None:
    model = GameModel(rng=Random(5))
    player = model.player(0)
    player.hand = [ActionCardState.from_def(ACTION_CATALOG["sweet_madame"]) for _ in range(HAND_LIMIT)]
    player.deck = [ActionCardState.from_def(ACTION_CATALOG["paimon"])]
    model._draw_cards(player, 1)
    assert len(player.hand) == HAND_LIMIT
    for _ in range(ZONE_LIMIT + 1):
        model._push_support(player, ActionCardState.from_def(ACTION_CATALOG["dawn_winery"]))
        model._push_summon(player, SummonState.from_def(SUMMON_CATALOG["oz"]))
    assert len(player.supports) == ZONE_LIMIT
    assert len(player.summons) == ZONE_LIMIT


def test_end_phase_does_not_replay_summons_after_forced_switch() -> None:
    model = _open_action(GameModel(rng=Random(6)))
    p0 = model.player(0)
    p1 = model.player(1)
    p0.summons = [SummonState.from_def(SUMMON_CATALOG["baron_bunny"])]
    p1.characters[0].hp = 1
    assert model.apply(EndRound(0))
    assert model.apply(EndRound(1))
    assert model.phase == Phase.FORCED_SWITCH
    assert p1.characters[0].hp == 0
    usages_after = p0.summons[0].usages if p0.summons else 0
    assert usages_after == 0 or len(p0.summons) == 0
    assert model.apply(ForcedSwitch(1, 1))
    assert model.phase == Phase.REROLL
    assert model.round_number == 2


def test_tune_json_roundtrip() -> None:
    action = ElementalTuning(0, "abc", 2)
    restored = action_from_json(action_to_json(action))
    assert restored == action
    switch = SwitchCharacter(1, 2, (0,))
    assert action_from_json(action_to_json(switch)) == switch


def run_all() -> None:
    tests = [
        test_mulligan_replaces_once,
        test_phase_gate_and_fast_vs_combat,
        test_end_round_first_player_next_round,
        test_forced_switch_and_empty_deck,
        test_zone_and_hand_limits,
        test_end_phase_does_not_replay_summons_after_forced_switch,
        test_tune_json_roundtrip,
    ]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"{len(tests)} tests passed")


if __name__ == "__main__":
    run_all()
