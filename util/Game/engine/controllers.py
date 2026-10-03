from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from urllib.parse import urljoin

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
    action_from_json,
    action_to_json,
)
from util.Game.engine.dice import find_dice_payment
from util.Game.engine.game_model import GameModel
from util.Game.engine.types import CostKey, HitKind, HitRegion, Phase, PlayerId, SkillKind, UiSelection


class PlayerController(Protocol):
    player_id: PlayerId

    def poll(
        self,
        model: GameModel,
        clicks: Sequence[tuple[int, int]],
        hits: Sequence[HitRegion],
    ) -> Action | None: ...


class LocalPlayerController:
    """Builds Actions from Pygame click positions against view rectangles."""

    def __init__(self, player_id: PlayerId) -> None:
        self.player_id: PlayerId = player_id
        self.selection: UiSelection = UiSelection()

    def poll(
        self,
        model: GameModel,
        clicks: Sequence[tuple[int, int]],
        hits: Sequence[HitRegion],
    ) -> Action | None:
        if not model.waiting_on(self.player_id):
            return None
        for pos in clicks:
            target = self._hit_at(pos, hits)
            if target is None:
                continue
            action = self._on_hit(model, target)
            if action is not None:
                return action
        return None

    def _hit_at(self, pos: tuple[int, int], hits: Sequence[HitRegion]) -> HitRegion | None:
        for region in reversed(hits):
            if region.contains(pos):
                return region
        return None

    def _on_hit(self, model: GameModel, region: HitRegion) -> Action | None:
        kind = region.target.kind
        if kind == HitKind.HAND:
            iid = region.target.instance_id
            if iid in self.selection.hand_ids:
                self.selection.hand_ids.remove(iid)
            else:
                if model.phase != Phase.MULLIGAN:
                    self.selection.hand_ids.clear()
                self.selection.hand_ids.add(iid)
            return None
        if kind == HitKind.DIE:
            idx = region.target.index
            if idx in self.selection.die_indices:
                self.selection.die_indices.remove(idx)
            else:
                self.selection.die_indices.add(idx)
            return None
        if kind == HitKind.CHARACTER:
            idx = region.target.index
            if model.phase == Phase.SELECT_ACTIVE:
                return SelectActive(self.player_id, idx)
            if model.phase == Phase.FORCED_SWITCH:
                return ForcedSwitch(self.player_id, idx)
            self.selection.character_index = idx
            if model.phase == Phase.ACTION:
                if self.selection.hand_ids:
                    return self._try_play_card(model)
                return self._try_switch(model, idx)
            return None
        if kind == HitKind.SKILL and region.target.skill is not None:
            return self._try_skill(model, region.target.skill)
        if kind == HitKind.CONFIRM:
            return self._confirm(model)
        if kind == HitKind.END_ROUND:
            return EndRound(self.player_id)
        if kind == HitKind.TUNE:
            return self._try_tune(model)
        return None

    def _selected_dice(self) -> tuple[int, ...]:
        return tuple(sorted(self.selection.die_indices))

    def _payment(self, model: GameModel, cost: dict[CostKey, int]) -> tuple[int, ...] | None:
        chosen = self._selected_dice()
        if chosen:
            return chosen
        found = model.suggest_payment(self.player_id, cost)
        if found is None:
            return None
        return tuple(found)

    def _try_skill(self, model: GameModel, skill: SkillKind) -> Action | None:
        player = model.player(self.player_id)
        active = player.active()
        if active is None:
            return None
        cost = model.adjusted_skill_cost(active, skill)
        payment = self._payment(model, cost)
        if payment is None:
            return None
        return UseSkill(self.player_id, skill, payment)

    def _try_switch(self, model: GameModel, index: int) -> Action | None:
        player = model.player(self.player_id)
        if index == player.active_index:
            return None
        cost = model.switch_cost(player)
        payment = self._payment(model, cost)
        if payment is None:
            return None
        return SwitchCharacter(self.player_id, index, payment)

    def _try_tune(self, model: GameModel) -> Action | None:
        if len(self.selection.hand_ids) != 1 or len(self.selection.die_indices) != 1:
            return None
        card_id = next(iter(self.selection.hand_ids))
        die_index = next(iter(self.selection.die_indices))
        return ElementalTuning(self.player_id, card_id, die_index)

    def _confirm(self, model: GameModel) -> Action | None:
        if model.phase == Phase.MULLIGAN:
            return ConfirmMulligan(self.player_id, tuple(self.selection.hand_ids))
        if model.phase == Phase.REROLL:
            return ConfirmReroll(self.player_id, self._selected_dice())
        if model.phase == Phase.ACTION:
            return self._try_play_card(model)
        return None

    def _try_play_card(self, model: GameModel) -> Action | None:
        if len(self.selection.hand_ids) != 1:
            return None
        card_id = next(iter(self.selection.hand_ids))
        player = model.player(self.player_id)
        card = next((c for c in player.hand if c.instance_id == card_id), None)
        if card is None:
            return None
        payment = self._payment(model, dict(card.defn.cost))
        if payment is None:
            return None
        target = self.selection.character_index
        if target is None and player.active_index is not None:
            if card.kind == "equipment" or card.defn.heal > 0:
                target = player.active_index
        return PlayActionCard(self.player_id, card_id, payment, target)


class AIPlayerController:
    """Heuristic bot that only emits legal Action objects."""

    def __init__(self, player_id: PlayerId) -> None:
        self.player_id: PlayerId = player_id
        self._fast_plays: int = 0

    def poll(
        self,
        model: GameModel,
        clicks: Sequence[tuple[int, int]],
        hits: Sequence[HitRegion],
    ) -> Action | None:
        _ = clicks
        _ = hits
        if not model.waiting_on(self.player_id):
            self._fast_plays = 0
            return None
        if model.phase == Phase.MULLIGAN:
            return self._mulligan(model)
        if model.phase == Phase.SELECT_ACTIVE:
            return SelectActive(self.player_id, 0)
        if model.phase == Phase.REROLL:
            return self._reroll(model)
        if model.phase == Phase.FORCED_SWITCH:
            standbys = model.player(self.player_id).alive_standby_indices()
            if not standbys:
                return None
            return ForcedSwitch(self.player_id, standbys[0])
        if model.phase == Phase.ACTION:
            return self._action(model)
        return None

    def _mulligan(self, model: GameModel) -> ConfirmMulligan:
        player = model.player(self.player_id)
        discard: list[str] = []
        for card in player.hand:
            total = sum(v for k, v in card.defn.cost.items() if k != "energy")
            if total >= 3:
                discard.append(card.instance_id)
        return ConfirmMulligan(self.player_id, tuple(discard))

    def _reroll(self, model: GameModel) -> ConfirmReroll:
        player = model.player(self.player_id)
        active = player.active()
        want = active.element if active is not None else "omni"
        indices = [
            i for i, die in enumerate(player.dice) if die not in (want, "omni")
        ]
        return ConfirmReroll(self.player_id, tuple(indices))

    def _action(self, model: GameModel) -> Action:
        player = model.player(self.player_id)
        if self._fast_plays < 2:
            played = self._try_play_cheap(model)
            if played is not None:
                self._fast_plays += 1
                return played
        for skill in ("burst", "skill", "normal"):
            used = self._try_skill(model, skill)
            if used is not None:
                self._fast_plays = 0
                return used
        active = player.active()
        if active is not None and active.hp <= 4:
            switched = self._try_switch(model)
            if switched is not None:
                self._fast_plays = 0
                return switched
        self._fast_plays = 0
        return EndRound(self.player_id)

    def _try_skill(self, model: GameModel, skill: SkillKind) -> UseSkill | None:
        player = model.player(self.player_id)
        active = player.active()
        if active is None:
            return None
        cost = model.adjusted_skill_cost(active, skill)
        pay = find_dice_payment(player.dice, cost)
        if pay is None:
            return None
        action = UseSkill(self.player_id, skill, tuple(pay))
        if model.validate(action) is None:
            return action
        return None

    def _try_switch(self, model: GameModel) -> SwitchCharacter | None:
        player = model.player(self.player_id)
        cost = model.switch_cost(player)
        pay = find_dice_payment(player.dice, cost)
        if pay is None and cost:
            return None
        for index in player.alive_standby_indices():
            action = SwitchCharacter(self.player_id, index, tuple(pay or []))
            if model.validate(action) is None:
                return action
        return None

    def _try_play_cheap(self, model: GameModel) -> PlayActionCard | None:
        player = model.player(self.player_id)
        for card in player.hand:
            total = sum(v for k, v in card.defn.cost.items() if k != "energy")
            if total > 1:
                continue
            pay = find_dice_payment(player.dice, dict(card.defn.cost))
            if pay is None:
                continue
            target = player.active_index
            action = PlayActionCard(self.player_id, card.instance_id, tuple(pay), target)
            if model.validate(action) is None:
                return action
        return None


class RemotePlayerController:
    """Polls a REST endpoint for the opponent's Action JSON payloads."""

    def __init__(
        self,
        player_id: PlayerId,
        api_base_url: str,
        match_id: str,
        timeout_s: float = 0.35,
    ) -> None:
        self.player_id: PlayerId = player_id
        self.api_base_url: str = api_base_url.rstrip("/") + "/"
        self.match_id: str = match_id
        self.timeout_s: float = timeout_s
        self.last_seq: int = 0

    def _actions_url(self) -> str:
        return urljoin(self.api_base_url, f"matches/{self.match_id}/actions")

    def poll(
        self,
        model: GameModel,
        clicks: Sequence[tuple[int, int]],
        hits: Sequence[HitRegion],
    ) -> Action | None:
        _ = clicks
        _ = hits
        if not model.waiting_on(self.player_id):
            return None
        try:
            import requests
        except ImportError:
            return None
        try:
            response = requests.get(
                self._actions_url(),
                params={"after": str(self.last_seq), "player_id": str(self.player_id)},
                timeout=self.timeout_s,
            )
        except requests.RequestException:
            return None
        if response.status_code != 200:
            return None
        payload: object = response.json()
        if not isinstance(payload, dict):
            return None
        seq_raw = payload.get("seq")
        if isinstance(seq_raw, int):
            self.last_seq = seq_raw
        action_raw = payload.get("action")
        if not isinstance(action_raw, dict):
            return None
        typed: dict[str, object] = {str(k): v for k, v in action_raw.items()}
        try:
            action = action_from_json(typed)
        except ValueError:
            return None
        if action.player_id != self.player_id:
            return None
        return action

    def publish(self, action: Action) -> bool:
        try:
            import requests
        except ImportError:
            return False
        try:
            response = requests.post(
                self._actions_url(),
                json={"action": action_to_json(action)},
                timeout=self.timeout_s,
            )
        except requests.RequestException:
            return False
        return response.status_code in (200, 201, 204)

    def publish_state(self, model: GameModel) -> bool:
        try:
            import requests
        except ImportError:
            return False
        try:
            response = requests.put(
                urljoin(self.api_base_url, f"matches/{self.match_id}/state"),
                json=model.to_public_dict(),
                timeout=self.timeout_s,
            )
        except requests.RequestException:
            return False
        return response.status_code in (200, 201, 204)
