from __future__ import annotations

from collections.abc import Sequence
from random import Random

import pygame

from util.Game.engine.actions import Action
from util.Game.engine.controllers import (
    AIPlayerController,
    LocalPlayerController,
    PlayerController,
    RemotePlayerController,
)
from util.Game.engine.game_model import GameModel
from util.Game.engine.types import PlayerId, UiSelection
from util.Game.engine.view import BoardView


class TcgApp:
    """MVC shell: Pygame view + generic controllers driving a pure GameModel."""

    def __init__(
        self,
        p0: PlayerController | None = None,
        p1: PlayerController | None = None,
        seed: int | None = None,
    ) -> None:
        pygame.display.set_caption("Genius Invokation TCG Engine")
        self.screen: pygame.Surface = pygame.display.set_mode((960, 540))
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.model: GameModel = GameModel(rng=Random(seed) if seed is not None else None)
        self.view: BoardView = BoardView((960, 540))
        self.local: LocalPlayerController | None = None
        self.controllers: list[PlayerController] = [
            p0 if p0 is not None else LocalPlayerController(0),
            p1 if p1 is not None else AIPlayerController(1),
        ]
        for controller in self.controllers:
            if isinstance(controller, LocalPlayerController):
                self.local = controller

    def _publish_if_needed(self, action: Action) -> None:
        for controller in self.controllers:
            if isinstance(controller, RemotePlayerController) and action.player_id != controller.player_id:
                _ = controller.publish(action)
                _ = controller.publish_state(self.model)

    def _collect_clicks(self, events: Sequence[pygame.event.Event]) -> list[tuple[int, int]]:
        clicks: list[tuple[int, int]] = []
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicks.append(event.pos)
        return clicks

    def run(self) -> None:
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            local_id: PlayerId = self.local.player_id if self.local is not None else 0
            selection = self.local.selection if self.local is not None else UiSelection()
            hits = self.view.render(self.screen, self.model, local_id, selection)
            clicks = self._collect_clicks(events)
            for controller in self.controllers:
                action = controller.poll(self.model, clicks, hits)
                if action is None:
                    continue
                if self.model.apply(action):
                    if self.local is not None:
                        self.local.selection = UiSelection()
                    self._publish_if_needed(action)
                    break

            pygame.display.flip()
            _ = self.clock.tick(60)


def run_local_vs_ai(seed: int | None = None) -> None:
    _ = pygame.init()
    app = TcgApp(seed=seed)
    app.run()
    pygame.quit()
