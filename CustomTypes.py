from typing import Literal, TypeAlias, Callable

from pygame import Rect

# Custom Types
PageType: TypeAlias = Literal["global", "authenticate", "setting", "main_menu", "deck_menu", "battle", "test", "leaderboard"]


KeyState: TypeAlias = Literal["pressed", "holding", "released"]
MouseAction: TypeAlias = Literal["clicked", "unclick","exit", "enter", "holding", "released"]
ActionFunction: TypeAlias = Callable[[], None]
GetRectFunction: TypeAlias = Callable[[], Rect]
ConditionalFunction: TypeAlias = Callable[[], bool]

