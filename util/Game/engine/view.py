from __future__ import annotations

import pygame

from util.Game.engine.entities import PlayerState
from util.Game.engine.game_model import ZONE_LIMIT, GameModel
from util.Game.engine.types import (
    ELEMENT_COLORS,
    HitKind,
    HitRegion,
    HitTarget,
    Phase,
    PlayerId,
    SkillKind,
    UiSelection,
)


def _hit(rect: pygame.Rect, target: HitTarget) -> HitRegion:
    return HitRegion(rect.x, rect.y, rect.w, rect.h, target)


class BoardView:
    def __init__(self, size: tuple[int, int] = (960, 540)) -> None:
        self.width, self.height = size
        self.title_font: pygame.font.Font = pygame.font.SysFont("arial", 22)
        self.font: pygame.font.Font = pygame.font.SysFont("arial", 16)
        self.small: pygame.font.Font = pygame.font.SysFont("arial", 13)
        self.hits: list[HitRegion] = []

    def render(
        self,
        surface: pygame.Surface,
        model: GameModel,
        local_id: PlayerId,
        selection: UiSelection,
    ) -> list[HitRegion]:
        self.hits = []
        _ = surface.fill((28, 32, 44))
        self._text(surface, f"Round {model.round_number}  |  {model.phase.value.upper()}", (16, 10), self.title_font)
        waiting = " / ".join(
            model.player(pid).name for pid in (0, 1) if model.waiting_on(pid)
        )
        turn = model.player(model.current_player).name if model.phase == Phase.ACTION else waiting
        self._text(surface, f"Window: {turn or '-'}", (16, 36), self.font, (210, 210, 210))
        if model.winner is not None:
            self._text(surface, f"{model.player(model.winner).name} WINS", (380, 250), self.title_font, (255, 210, 70))

        opponent_id: PlayerId = 1 if local_id == 0 else 0
        self._draw_player_board(surface, model, opponent_id, local_id, selection, opponent=True)
        self._draw_player_board(surface, model, local_id, local_id, selection, opponent=False)
        self._draw_buttons(surface, model)
        self._draw_log(surface, model)
        return self.hits

    def _draw_player_board(
        self,
        surface: pygame.Surface,
        model: GameModel,
        player_id: PlayerId,
        local_id: PlayerId,
        selection: UiSelection,
        *,
        opponent: bool,
    ) -> None:
        player = model.player(player_id)
        char_y = 70 if opponent else 250
        self._draw_characters(surface, player, player_id, local_id, selection, char_y, opponent)
        self._draw_zones(surface, player, opponent)
        if opponent:
            self._draw_hidden_hand(surface, player)
        else:
            self._draw_hand(surface, player, selection)
            self._draw_dice(surface, player, selection)
            self._draw_skills(surface, player)

    def _draw_characters(
        self,
        surface: pygame.Surface,
        player: PlayerState,
        player_id: PlayerId,
        local_id: PlayerId,
        selection: UiSelection,
        y: int,
        opponent: bool,
    ) -> None:
        order = self._character_layout_order(player)
        xs = [250, 400, 550]
        for slot, char_index in enumerate(order):
            character = player.characters[char_index]
            is_active = player.active_index == char_index
            w, h = (130, 160) if is_active else (100, 128)
            x = xs[slot]
            if not is_active:
                x += 15
                y_off = 16
            else:
                y_off = 0
            rect = pygame.Rect(x, y + y_off, w, h)
            color = ELEMENT_COLORS[character.element]
            if not character.alive:
                color = (70, 70, 70)
            pygame.draw.rect(surface, color, rect)
            selected = (not opponent) and selection.character_index == char_index
            border = (255, 230, 80) if selected or is_active else (20, 20, 20)
            pygame.draw.rect(surface, border, rect, 3 if is_active else 2)
            self._text(surface, character.name, (rect.x + 6, rect.y + 6), self.small, (10, 10, 10))
            self._text(surface, f"HP {character.hp}/{character.max_hp}", (rect.x + 6, rect.y + 24), self.small, (10, 10, 10))
            self._text(surface, f"EN {character.energy}/{character.max_energy}", (rect.x + 6, rect.y + 40), self.small, (10, 10, 10))
            self._text(surface, character.element.upper(), (rect.x + 6, rect.y + 56), self.small, (10, 10, 10))
            self._text(surface, character.weapon, (rect.x + 6, rect.y + 72), self.small, (10, 10, 10))
            if character.equipment is not None:
                self._text(surface, character.equipment.name[:12], (rect.x + 6, rect.y + 90), self.small, (20, 20, 20))
            kind = HitKind.OPPONENT_CHARACTER if opponent else HitKind.CHARACTER
            self.hits.append(_hit(rect, HitTarget(kind, char_index, player_id=player_id)))

    def _character_layout_order(self, player: PlayerState) -> list[int]:
        if player.active_index is None:
            return [0, 1, 2]
        rest = [i for i in range(3) if i != player.active_index]
        if len(rest) == 2:
            return [rest[0], player.active_index, rest[1]]
        return [player.active_index, *rest]

    def _draw_zones(self, surface: pygame.Surface, player: PlayerState, opponent: bool) -> None:
        y = 70 if opponent else 250
        for i in range(ZONE_LIMIT):
            rect = pygame.Rect(16, y + i * 40, 90, 36)
            pygame.draw.rect(surface, (54, 60, 78), rect)
            pygame.draw.rect(surface, (140, 140, 160), rect, 1)
            if i < len(player.supports):
                self._text(surface, player.supports[i].name[:10], (rect.x + 4, rect.y + 10), self.small)
            else:
                self._text(surface, "Support", (rect.x + 4, rect.y + 10), self.small, (110, 110, 130))
        for i in range(ZONE_LIMIT):
            rect = pygame.Rect(680, y + i * 40, 90, 36)
            pygame.draw.rect(surface, (54, 60, 78), rect)
            pygame.draw.rect(surface, (140, 140, 160), rect, 1)
            if i < len(player.summons):
                s = player.summons[i]
                self._text(surface, f"{s.name[:9]} {s.usages}", (rect.x + 4, rect.y + 10), self.small)
            else:
                self._text(surface, "Summon", (rect.x + 4, rect.y + 10), self.small, (110, 110, 130))

    def _draw_hand(self, surface: pygame.Surface, player: PlayerState, selection: UiSelection) -> None:
        width = 78
        start = 180
        for i, card in enumerate(player.hand):
            rect = pygame.Rect(start + i * (width + 8), 430, width, 100)
            color = (168, 168, 186)
            pygame.draw.rect(surface, color, rect)
            border = (255, 80, 80) if card.instance_id in selection.hand_ids else (255, 255, 255)
            pygame.draw.rect(surface, border, rect, 3)
            self._text(surface, card.name[:9], (rect.x + 4, rect.y + 8), self.small, (10, 10, 10))
            self._text(surface, card.kind, (rect.x + 4, rect.y + 26), self.small, (20, 20, 20))
            cost = ",".join(f"{k[:2]}{v}" for k, v in card.defn.cost.items())
            self._text(surface, cost, (rect.x + 4, rect.y + 44), self.small, (20, 20, 20))
            self.hits.append(_hit(rect, HitTarget(HitKind.HAND, i, card.instance_id, player_id=player.player_id)))
        if not player.hand:
            self._text(surface, "Empty hand", (start, 460), self.font, (160, 160, 160))

    def _draw_hidden_hand(self, surface: pygame.Surface, player: PlayerState) -> None:
        for i in range(len(player.hand)):
            rect = pygame.Rect(180 + i * 22, 16, 18, 28)
            pygame.draw.rect(surface, (90, 90, 110), rect)
            pygame.draw.rect(surface, (200, 200, 220), rect, 1)

    def _draw_dice(self, surface: pygame.Surface, player: PlayerState, selection: UiSelection) -> None:
        for i, die in enumerate(player.dice):
            col = i // 8
            row = i % 8
            rect = pygame.Rect(868 + col * 42, 70 + row * 42, 36, 36)
            pygame.draw.rect(surface, ELEMENT_COLORS[die], rect)
            border = (255, 40, 40) if i in selection.die_indices else (0, 0, 0)
            pygame.draw.rect(surface, border, rect, 3)
            label_color = (20, 20, 20) if die != "omni" else (40, 40, 40)
            self._text(surface, die[:2].upper(), (rect.x + 4, rect.y + 10), self.small, label_color)
            self.hits.append(_hit(rect, HitTarget(HitKind.DIE, i, player_id=player.player_id)))

    def _draw_skills(self, surface: pygame.Surface, player: PlayerState) -> None:
        active = player.active()
        if active is None:
            return
        labels: list[tuple[SkillKind, str]] = [
            ("normal", "NA"),
            ("skill", "Skill"),
            ("burst", "Burst"),
        ]
        for i, (kind, label) in enumerate(labels):
            rect = pygame.Rect(790, 410 + i * 32, 150, 28)
            pygame.draw.rect(surface, (72, 86, 118), rect)
            pygame.draw.rect(surface, (220, 220, 230), rect, 1)
            skill = active.skill(kind)
            self._text(surface, f"{label}: {skill.name[:12]}", (rect.x + 6, rect.y + 6), self.small)
            self.hits.append(_hit(rect, HitTarget(HitKind.SKILL, i, skill=kind, player_id=player.player_id)))

    def _draw_buttons(self, surface: pygame.Surface, model: GameModel) -> None:
        confirm = pygame.Rect(16, 500, 110, 28)
        end_round = pygame.Rect(136, 500, 110, 28)
        tune = pygame.Rect(256, 500, 110, 28)
        for rect, label, kind in (
            (confirm, "Confirm", HitKind.CONFIRM),
            (end_round, "End Round", HitKind.END_ROUND),
            (tune, "Tune", HitKind.TUNE),
        ):
            pygame.draw.rect(surface, (196, 196, 204), rect)
            pygame.draw.rect(surface, (20, 20, 20), rect, 2)
            self._text(surface, label, (rect.x + 10, rect.y + 6), self.small, (10, 10, 10))
            self.hits.append(_hit(rect, HitTarget(kind)))
        hint = self._hint(model)
        self._text(surface, hint, (380, 504), self.small, (200, 200, 210))

    def _hint(self, model: GameModel) -> str:
        if model.phase == Phase.MULLIGAN:
            return "Click cards to replace, then Confirm."
        if model.phase == Phase.SELECT_ACTIVE:
            return "Click a character to make them Active."
        if model.phase == Phase.REROLL:
            return "Click dice to reroll, then Confirm."
        if model.phase == Phase.FORCED_SWITCH:
            return "Active character fell. Click a standby."
        if model.phase == Phase.ACTION:
            return "Skills/Switch pass the turn. Cards/Tune do not."
        if model.phase == Phase.GAME_OVER:
            return "Match finished."
        return ""

    def _draw_log(self, surface: pygame.Surface, model: GameModel) -> None:
        lines = model.log[-5:]
        y = 418
        for line in lines:
            self._text(surface, line[:52], (16, y), self.small, (170, 176, 190))
            y += 14

    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: tuple[int, int],
        font: pygame.font.Font,
        color: tuple[int, int, int] = (245, 245, 245),
    ) -> None:
        img = font.render(text, True, color)
        _ = surface.blit(img, pos)
