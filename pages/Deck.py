

from components.Image import ImageComponent

from pygame.surface import Surface

from components.Draggable import DraggableComponent

from pygame.surface import Surface

from components.Image import TextImageComponent

from pygame.rect import Rect


from pygame import Font, Surface
import pygame

from components import DropDown, ImageOption
from components.TextInput import TextInput
from components.Image import ImageComponent, TextImageComponent, TextOption
from components.Button import Button
from components.Draggable import DraggableComponent
from util.GlobalHolder import GlobalHolder
from util.Game.Card import ActionCard, CharacterCard
from util.Game.Player import DeckData, Player, UserInfo
from typing import Any, override, final, TypeAlias, Literal

from util.Game.Card import CHARACTER_DB, ACTION_DB
# --- DECK PAGE IMPLEMENTATION ---
DeckSubEvents: TypeAlias = Literal["deck_list", "deck_preview_char", "deck_preview_action", "edit_deck_name"]


from pages.BasePage import BasePage


class DeckPage(BasePage):
    @final
    def __init__(self) -> None:
        if not GlobalHolder.player:
            raise ValueError("Player not found")
        # Use a small sample player template when the page is opened without saved data.
        self.deck_sub_events: dict[DeckSubEvents, bool] = {"deck_list": True, "deck_preview_char": False, "deck_preview_action": False, "edit_deck_name": False}
        # Temporary way of showing the number of characters
        self.database_chars: list[str] = [char["name"] for char in CHARACTER_DB.values()]
        self.database_actions: list[str] = [action["name"] for action in ACTION_DB.values()]

        # This is populated when a deck is selected for editing or previewing.
        self.selected_deck_edit: DeckData
        self.saved_deck_snapshot: DeckData | None = None
        self.editing_deck_index: int | None = None
        self.renaming_deck_index: int | None = None
        self.deck_dirty: bool = False

        # Top-left positions for the four deck slots on the deck menu.
        self.deck_positions: list[tuple[int, int]] = [(24, 80), (254, 80), (492, 80), (726, 80)]
        super().__init__()

        # Start on the main deck list rather than a preview screen.
        self.change_page(new_state="deck_menu")
    

    @override
    def init(self) -> None:
        super().init()
        self.init_background(image_key="background_image4")

        self.card_selector_background: ImageComponent = ImageComponent(image_option=self.load_image(image_key="card_selector"), base_pos=(480, 270), anchor="center") # pyright: ignore
        self.card_placeholder: ImageComponent = ImageComponent(image_option=self.load_image(image_key="card_placeholder"), base_pos=(480, 140), anchor="center") # pyright: ignore
        self.decks: list[tuple[ImageComponent, ImageComponent | None, TextImageComponent | None, DropDown | None]] = [] # pyright: ignore
        #                     The deck image,  the card image       , Deck Name                , Drop downs

        for i in range(0, 4):
            # Check if the deck slot is unlocked for the player. If it is, create an active deck box; if not, create a locked deck box with a message.
            if GlobalHolder.player.is_deck_slot_unlocked(slot_no=i):

                deck: ImageComponent = ImageComponent(image_option="deck_box_active", base_pos=self.deck_positions[i])
                deck.update_layout()
                character_surface: ImageComponent | None = None
                text_surface: TextImageComponent | None = None
                
                if (i < len(GlobalHolder.player.user_decks)) and GlobalHolder.player.user_decks[i].get("characters", []):
                    character_surface = ImageComponent(
                        image_option=self.draw_deck_card(cards=GlobalHolder.player.user_decks[i].get("characters")), 
                        base_pos=(deck.rect.centerx, int(deck.rect.centery * 0.8)), anchor="center")
                    
                    text_surface = TextImageComponent(text_option=TextOption(text=GlobalHolder.player.user_decks[i].get("name"), size=20, align="center", max_width=int(deck.rect.width * 0.9)), base_pos=(deck.rect.centerx, deck.rect.y + int(deck.rect.height * 0.7)), anchor="center")
                
                #menu_surface: ImageComponent =  ImageComponent(image_option="menu_dots", base_pos=(int(deck.rect.x + int(deck.rect.width * 0.97)), deck.rect.y + int(deck.rect.height * 0.03)) , anchor="topright")
                menu: DropDown = DropDown(
                    items=["Save As Active Deck", "Edit Deck Name", "Preview/Edit Deck", "Delete Deck"],
                    dropdown_surface=ImageComponent(image_option="menu_dots", base_pos=(int(deck.rect.x + int(deck.rect.width * 0.97)), deck.rect.y + int(deck.rect.height * 0.03)) , anchor="topright"),
                    item_sizes=(125, 18), menu_position=deck.rect.topright, menu_anchor="topleft"
                    )

                menu.on_change = lambda idx=i, m=menu: self.menu_handle(deck_index=idx, action=m.selected_item)
                
        
                self.decks.append((deck, character_surface, text_surface, menu))
            else:
                deck = ImageComponent(image_option="locked_deck", base_pos=self.deck_positions[i])
                deck.update_layout()
                text_surface = TextImageComponent(text_option=TextOption(text=f"Unlocks at level {i+1}", size=15, align="center", max_width=int(deck.rect.width * 0.9), color=(240, 240, 250)), base_pos=(deck.rect.centerx, deck.rect.y + int(deck.rect.height * 0.7)), anchor="center")
                self.decks.append((deck, None, text_surface, None))

        
        self.top_character_cards: list[DraggableComponent] = [] # pyright: ignore
        self.bottom_character_cards: list[DraggableComponent] = [] # pyright: ignore

        self.top_action_cards: list[DraggableComponent] = [] # pyright: ignore
        self.bottom_action_cards: list[DraggableComponent] = [] # pyright: ignore

        self.deck_button_placeholder: ImageComponent = ImageComponent(image_option=self.load_image(image_key="deck_button_placeholder"), base_pos=(0,0), anchor="topleft") # pyright: ignore[reportUninitializedInstanceVariable]

        self.character_deck_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="deck_button_character")), text_option=TextOption(text="", size=0), position=(5, 32), anchor="topleft") # pyright: ignore[reportUninitializedInstanceVariable]
        self.action_deck_button: Button = Button(image_option=ImageOption(image=self.load_image(image_key="deck_button_action")), text_option=TextOption(text="", size=0), position=(5, 87), anchor="topleft") # pyright: ignore[reportUninitializedInstanceVariable]
        self.exit_button: Button = Button(image_option=ImageOption(colored_image=((255, 0, 0), (36, 36))), text_option=TextOption(text="", size=0), position=(0, 504), anchor="topleft") # pyright: ignore[reportUninitializedInstanceVariable]
        self.save_deck_button: Button = Button(
            image_option=ImageOption(colored_image=((82, 100, 121), (160, 42)), round_edges=12),
            text_option=TextOption(text="Save", size=16, color=(166, 166, 166)),
            position=(940, 504),
            anchor="topright",
        )
        self.save_deck_button.on_activate = self.save_deck_changes

        self.rename_overlay: ImageComponent = ImageComponent(image_option="confirmation_overlay", base_pos=(480, 243), anchor="center")
        self.rename_title: TextImageComponent = TextImageComponent(
            text_option=TextOption(text="Change Deck Name", size=24, align="center", bold=True),
            base_pos=(480, 170),
            anchor="center",
        )
        self.rename_input: TextInput = TextInput(
            image_option=ImageOption(image=self.load_image(image_key="text_input1")),
            text_option=TextOption(text="", size=16, color=(128, 103, 89)),
            placeholder="Deck name",
            position=(480, 230),
            anchor="center",
            max_length=16,
        )
        self.rename_input.validations = [
            (lambda text: 3 <= len(text.strip()) <= 16, "Name must be 3-16 characters"),
            (self._rename_is_unique, "That name is already used"),
            (lambda text: all(character.isalnum() or character.isspace() for character in text), "Use letters, numbers and spaces only"),
        ]
        self.rename_save_button: Button = Button(
            image_option=ImageOption(image=self.load_image(image_key="button1")),
            text_option=TextOption(text="Save", size=16),
            position=(348, 326),
            anchor="center",
        )
        self.rename_cancel_button: Button = Button(
            image_option=ImageOption(image=self.load_image(image_key="button1")),
            text_option=TextOption(text="Cancel", size=16),
            position=(612, 326),
            anchor="center",
        )
        self.rename_save_button.on_activate = self.confirm_rename_deck
        self.rename_cancel_button.on_activate = self.cancel_rename_deck
    def handle_card_drop(self, dropped_card: DraggableComponent, card_list: list[DraggableComponent]) -> None:
        """Handles the 1-to-1 swap between cards (or empty slots)."""
        print(f"Handling drop for card with data_key: {dropped_card.data_key}")
        target: DraggableComponent | None = dropped_card.check_collision(others=card_list)
        
        if target:
            print(f"Collision detected! Swapping {dropped_card.data_key} with {target.data_key}")
            
            # 1. Correctly swap data keys and images without overwriting
            temp_key: str | None = dropped_card.data_key
            temp_img: Surface = dropped_card.surface._raw_image
            
            dropped_card.data_key = target.data_key
            dropped_card.surface._raw_image = target.surface._raw_image
            
            target.data_key = temp_key
            target.surface._raw_image = temp_img
            
            # 2. Handle Character Cards updating
            if self.deck_sub_events.get("deck_preview_char"):
                # Convert None back to "dummy" before saving to the deck
                current_deck: list[Any | str] = [card.data_key if card.data_key is not None else "dummy" for card in self.top_character_cards]
                self.selected_deck_edit.update(characters=current_deck)

                # 3. A bottom card dropped onto an empty slot leaves a dummy behind, so refill or remove it
                if dropped_card in self.bottom_character_cards and dropped_card.data_key in (None, "dummy"):
                    if not self.replace_or_remove_bottom_card(dropped_card=dropped_card, card_type="char"):
                        target.update_layout()
                        return

            # 4. Handle Action Cards updating
            elif self.deck_sub_events.get("deck_preview_action"):
                # Convert None back to "dummy" before saving to the deck
                current_deck: list[Any | str] = [card.data_key if card.data_key is not None else "dummy" for card in self.top_action_cards]
                self.selected_deck_edit.update(action_cards=current_deck)

                # 5. A bottom card dropped onto an empty slot leaves a dummy behind, so refill or remove it
                if dropped_card in self.bottom_action_cards and dropped_card.data_key in (None, "dummy"):
                    if not self.replace_or_remove_bottom_card(dropped_card=dropped_card, card_type="action"):
                        target.update_layout()
                        return

            self._refresh_deck_dirty()

            # Force target to snap into its updated state
            target.update_layout()

        # Snap the dropped card back to its home (which remained the same physical coordinate)
        dropped_card.update_layout()

    def replace_or_remove_bottom_card(self, dropped_card: DraggableComponent, card_type: Literal["char", "action"]) -> bool:
        """Fills the bottom slot with an unused card. Returns False if the slot was removed instead."""
        if card_type == "char":
            top_cards, bottom_cards, all_keys = self.top_character_cards, self.bottom_character_cards, list(CHARACTER_DB.keys())
        else:
            top_cards, bottom_cards, all_keys = self.top_action_cards, self.bottom_action_cards, list(ACTION_DB.keys())

        used_keys: list[str] = [card.data_key for card in top_cards + bottom_cards if card.data_key not in (None, "dummy")]
        available_keys: list[str] = [key for key in all_keys if key not in used_keys]

        if available_keys:
            new_key: str = available_keys[0]
            dropped_card.data_key = new_key
            if card_type == "char":
                dropped_card.surface._raw_image = self.get_character_card_surface(character_key=new_key, card_type="char")
            else:
                dropped_card.surface._raw_image = self.get_action_card_surface(card_key=new_key)
            # The old outline was built from the previous image
            dropped_card.surface.outline_image = None
            return True

        # Nothing left to show, so take the card off screen and close the gap
        bottom_cards.remove(dropped_card)
        dropped_card.surface.outline_image = None
        self.reposition_bottom_cards(card_type=card_type)
        return False

    @staticmethod
    def bottom_card_position(index: int, card_type: Literal["char", "action"]) -> tuple[int, int]:
        if card_type == "char":
            return ((index * 179) + 82, 285)
        return ((index * 84) + 67, 285)

    def reposition_bottom_cards(self, card_type: Literal["char", "action"]) -> None:
        bottom_cards: list[DraggableComponent] = self.bottom_character_cards if card_type == "char" else self.bottom_action_cards
        for index, card in enumerate(bottom_cards):
            card.set_home(new_pos=self.bottom_card_position(index=index, card_type=card_type))
    
    def setup_cards(self, type: Literal["char", "action"]) -> None:
        if type == "char":
            self.top_character_cards.clear()
            self.bottom_character_cards.clear()
            
            # 1. Use .copy() to prevent modifying the actual player deck data when appending "dummy"
            player_cards: list[str] = self.selected_deck_edit.get("characters", []).copy()

            if len(player_cards) != 3: 
                while len(player_cards) < 3: 
                    player_cards.append("dummy")  # Fill with dummy for empty slots

            for i, character_key in enumerate(player_cards):
                card: DraggableComponent = DraggableComponent(
                    image=self.get_character_card_surface(character_key=character_key, card_type="char"),
                    base_pos=((i * 220) + 223, 75),
                    anchor="topleft",
                    data_key=character_key if character_key != "dummy" else None
                )
                card.on_drop = lambda dropped_card=card: self.handle_card_drop(dropped_card=dropped_card, card_list=self.top_character_cards)
                self.top_character_cards.append(card)

            # 2. FIX: Iterate over keys, not values, so we pass the correct ID to the surface generator
            available_chars: list[str] = [key for key in CHARACTER_DB.keys() if key not in player_cards]
            
            for i, character_key in enumerate(available_chars[:5]):  # Limit to 5 for the bottom row
                card = DraggableComponent(
                    image=self.get_character_card_surface(character_key=character_key, card_type="char"),
                    base_pos=self.bottom_card_position(index=i, card_type="char"),
                    anchor="topleft",
                    data_key=character_key
                )
                card.on_drop = lambda dropped_card=card: self.handle_card_drop(dropped_card=dropped_card, card_list=self.top_character_cards)
                self.bottom_character_cards.append(card)

            for card in self.top_character_cards + self.bottom_character_cards:
                # Removed cards keep their listeners, so check the card is still on screen
                card.add_event_listeners(page_state="deck_menu", condition=lambda c=card: self.deck_sub_events["deck_preview_char"] and (c in self.top_character_cards or c in self.bottom_character_cards))
                
        elif type == "action":
            self.top_action_cards.clear()
            self.bottom_action_cards.clear()
            
            # 1. Use .copy() here as well
            action_cards: list[str] = self.selected_deck_edit.get("action_cards", []).copy()

            if len(action_cards) != 10:
                while len(action_cards) < 10: 
                    action_cards.append("dummy")  # Fill with dummy for empty slots

            for i, action_key in enumerate(action_cards):
                card = DraggableComponent(
                    image=self.get_action_card_surface(card_key=action_key),
                    base_pos=((i * 84) + 67, 75),
                    anchor="topleft",
                    data_key=action_key if action_key != "dummy" else None
                )
                card.on_drop = lambda dropped_card=card: self.handle_card_drop(dropped_card=dropped_card, card_list=self.top_action_cards)
                self.top_action_cards.append(card)

            # 2. FIX: Iterate over keys instead of values
            available_action: list[str] = [key for key in ACTION_DB.keys() if key not in action_cards]
            
            for i, action_key in enumerate(available_action[:10]):  # Limit to 10 for the bottom row
                card = DraggableComponent(
                    image=self.get_action_card_surface(card_key=action_key),
                    base_pos=self.bottom_card_position(index=i, card_type="action"),
                    anchor="topleft",
                    data_key=action_key
                )
                card.on_drop = lambda dropped_card=card: self.handle_card_drop(dropped_card=dropped_card, card_list=self.top_action_cards)
                self.bottom_action_cards.append(card)
                
            for card in self.top_action_cards + self.bottom_action_cards:
                # Removed cards keep their listeners, so check the card is still on screen
                card.add_event_listeners(page_state="deck_menu", condition=lambda c=card: self.deck_sub_events["deck_preview_action"] and (c in self.top_action_cards or c in self.bottom_action_cards))

            
    def menu_handle(self, deck_index: int = 0, action: str | None = None) -> None:
        print(f"Deck {deck_index} selected with action: {action}")
        if not action: return

        

        if action == "Save As Active Deck":
            GlobalHolder.player.user_info.update(active_deck_uid=GlobalHolder.player.user_decks[deck_index].get("uid"))
        elif action == "Edit Deck Name":
            self.open_rename_deck(deck_index=deck_index)
        elif action == "Delete Deck":
            self.selected_deck_edit = GlobalHolder.player.user_decks[deck_index]
            self.selected_deck_edit.update(name="")
            self.selected_deck_edit.update(characters=[])
            self.selected_deck_edit.update(action_cards=[])
            GlobalHolder.player.user_decks[deck_index] = self.selected_deck_edit
        elif action == "Preview/Edit Deck":
            self.deck_sub_events["deck_list"] = False
            self.deck_sub_events["deck_preview_char"] = True
            self.editing_deck_index = deck_index
            self.selected_deck_edit = self._copy_deck(deck=GlobalHolder.player.user_decks[deck_index])
            self.saved_deck_snapshot = self._copy_deck(deck=self.selected_deck_edit)
            self.deck_dirty = False
            self._update_save_button_ui()

            print(f"Selected deck for editing: {self.selected_deck_edit.get('name')}")
            self.setup_cards(type="char")
            self.setup_cards(type="action")

    def _copy_deck(self, deck: DeckData) -> DeckData:
        return DeckData(
            user_id=deck.get("user_id", ""),
            uid=deck.get("uid", ""),
            name=deck.get("name", ""),
            characters=list(deck.get("characters", [])),
            action_cards=list(deck.get("action_cards", [])),
        )

    @staticmethod
    def _real_cards(cards: list[str]) -> list[str]:
        return [card for card in cards if card and card != "dummy"]

    def _deck_signature(self, deck: DeckData) -> tuple[tuple[str, ...], tuple[str, ...], str]:
        return (
            tuple(self._real_cards(cards=deck.get("characters", []))),
            tuple(self._real_cards(cards=deck.get("action_cards", []))),
            deck.get("name", ""),
        )

    def _preview_is_open(self) -> bool:
        return self.deck_sub_events["deck_preview_char"] or self.deck_sub_events["deck_preview_action"]

    def _save_button_is_active(self) -> bool:
        return self._preview_is_open() and self.deck_dirty

    def _update_save_button_ui(self) -> None:
        if self.deck_dirty:
            self.save_deck_button.text_surface.text_option.set_color(color=(255, 255, 255))
        else:
            self.save_deck_button.text_surface.text_option.set_color(color=(166, 166, 166))
        self.save_deck_button.update_layout()

    def _refresh_deck_dirty(self) -> None:
        if self.saved_deck_snapshot is None:
            self.deck_dirty = False
        else:
            self.deck_dirty = self._deck_signature(deck=self.selected_deck_edit) != self._deck_signature(deck=self.saved_deck_snapshot)
        self._update_save_button_ui()

    def _refresh_deck_slot(self, deck_index: int) -> None:
        if GlobalHolder.player is None or not 0 <= deck_index < len(self.decks):
            return
        bg, _, _, menu = self.decks[deck_index]
        deck: DeckData = GlobalHolder.player.user_decks[deck_index]
        characters: list[str] = self._real_cards(cards=deck.get("characters", []))
        character_surface: ImageComponent | None = None
        text_surface: TextImageComponent | None = None
        if characters:
            character_surface = ImageComponent(
                image_option=self.draw_deck_card(cards=characters),
                base_pos=(bg.rect.centerx, int(bg.rect.centery * 0.8)),
                anchor="center",
            )
            character_surface.update_layout()
        name: str = deck.get("name", "")
        if name:
            text_surface = TextImageComponent(
                text_option=TextOption(text=name, size=20, align="center", max_width=int(bg.rect.width * 0.9)),
                base_pos=(bg.rect.centerx, bg.rect.y + int(bg.rect.height * 0.7)),
                anchor="center",
            )
            text_surface.update_layout()
        self.decks[deck_index] = (bg, character_surface, text_surface, menu)

    def save_deck_changes(self) -> None:
        if not self.deck_dirty or self.editing_deck_index is None or GlobalHolder.player is None:
            return

        self.selected_deck_edit["characters"] = self._real_cards(cards=self.selected_deck_edit.get("characters", []))
        self.selected_deck_edit["action_cards"] = self._real_cards(cards=self.selected_deck_edit.get("action_cards", []))
        GlobalHolder.player.user_decks[self.editing_deck_index] = self._copy_deck(deck=self.selected_deck_edit)
        if GlobalHolder.player.user_info.get("active_deck_uid") == self.selected_deck_edit.get("uid"):
            GlobalHolder.player.selected_deck = GlobalHolder.player.user_decks[self.editing_deck_index]

        self.db.update_deck(deck_id=self.selected_deck_edit["uid"], deck_data=self.selected_deck_edit)
        self.saved_deck_snapshot = self._copy_deck(deck=self.selected_deck_edit)
        self.deck_dirty = False
        self._update_save_button_ui()
        self._refresh_deck_slot(deck_index=self.editing_deck_index)

    def _rename_overlay_open(self) -> bool:
        return self.deck_sub_events.get("edit_deck_name", False)

    def _rename_is_unique(self, name: str) -> bool:
        if GlobalHolder.player is None or self.renaming_deck_index is None:
            return True
        cleaned: str = name.strip().lower()
        for index, deck in enumerate(GlobalHolder.player.user_decks):
            if index != self.renaming_deck_index and deck.get("name", "").strip().lower() == cleaned:
                return False
        return True

    def open_rename_deck(self, deck_index: int) -> None:
        if GlobalHolder.player is None or not 0 <= deck_index < len(GlobalHolder.player.user_decks):
            return
        self.renaming_deck_index = deck_index
        self.deck_sub_events["edit_deck_name"] = True
        current_name: str = GlobalHolder.player.user_decks[deck_index].get("name", "")
        self.rename_input.set_text(text=current_name)
        self.rename_input._enable_typing()

    def cancel_rename_deck(self) -> None:
        self.rename_input._disable_typing()
        self.deck_sub_events["edit_deck_name"] = False
        self.renaming_deck_index = None

    def confirm_rename_deck(self) -> None:
        if GlobalHolder.player is None or self.renaming_deck_index is None:
            return
        name: str = self.rename_input.text.strip()
        self.rename_input.validate_text(text=name)
        if not self.rename_input.valid:
            return

        deck: DeckData = GlobalHolder.player.user_decks[self.renaming_deck_index]
        deck["name"] = name
        if GlobalHolder.player.selected_deck is not None and GlobalHolder.player.selected_deck.get("uid") == deck.get("uid"):
            GlobalHolder.player.selected_deck["name"] = name
        if self.editing_deck_index == self.renaming_deck_index:
            self.selected_deck_edit["name"] = name
            if self.saved_deck_snapshot is not None:
                self.saved_deck_snapshot["name"] = name
            self._refresh_deck_dirty()

        self.db.update_deck(deck_id=deck["uid"], deck_data=deck)
        self._refresh_deck_slot(deck_index=self.renaming_deck_index)
        self.cancel_rename_deck()

    def conditional_exit(self) -> None:
        if self._rename_overlay_open():
            self.cancel_rename_deck()
            return
        if self.deck_sub_events["deck_preview_char"] or self.deck_sub_events["deck_preview_action"]:
            self.deck_sub_events["deck_preview_char"] = False
            self.deck_sub_events["deck_preview_action"] = False
            self.deck_sub_events["deck_list"] = True
            self.deck_dirty = False
            self._update_save_button_ui()
        else:
            self.change_page(new_state="main_menu")
        

    @override
    def add_events(self) -> None:
        
        super().add_events()
        self.exit_button.on_activate = self.conditional_exit
        self.exit_button.add_event_listeners(page_state="deck_menu")

        def show_character_preview() -> None:
            self.deck_sub_events["deck_preview_char"] = True
            self.deck_sub_events["deck_preview_action"] = False

        def show_action_preview() -> None:
            self.deck_sub_events["deck_preview_char"] = False
            self.deck_sub_events["deck_preview_action"] = True

        self.action_deck_button.on_activate = show_action_preview
        self.character_deck_button.on_activate = show_character_preview
        self.character_deck_button.add_event_listeners(page_state="deck_menu", condition=lambda: self._preview_is_open() and not self._rename_overlay_open())

        self.action_deck_button.add_event_listeners(page_state="deck_menu", condition=lambda: self._preview_is_open() and not self._rename_overlay_open())
        self.save_deck_button.add_event_listeners(page_state="deck_menu", condition=self._save_button_is_active)

        self.rename_input.add_event_listeners(page_state="deck_menu", condition=self._rename_overlay_open)
        self.rename_save_button.add_event_listeners(page_state="deck_menu", condition=lambda: self._rename_overlay_open() and self.rename_input.valid)
        self.rename_cancel_button.add_event_listeners(page_state="deck_menu", condition=self._rename_overlay_open)

        for _, _, _, menu in self.decks:
            if menu:
                menu.add_event_listeners(page_state="deck_menu", condition=lambda: self.deck_sub_events["deck_list"] and not self._rename_overlay_open())
        # As you add buttons (like a back button) or dropdowns for each deck later, 

        # their event listener initializations will go here.
        pass

    @override
    def update_layout(self) -> None:
        super().update_layout()
        
        # Iterates through the stored lists to update Pygame rects and positions
        for deck in self.decks:
            bg, char_surf, text_surf, menu = deck
            bg.update_layout()
            if char_surf: char_surf.update_layout()
            if text_surf: text_surf.update_layout()
            if menu: menu.update_layout()
        
        if self.top_action_cards:
            for card in self.top_action_cards:
                card.update_layout()
        if self.bottom_action_cards:
            for card in self.bottom_action_cards:
                card.update_layout()
        
        if self.top_character_cards:
            for card in self.top_character_cards:
                card.update_layout()
        
        if self.bottom_character_cards:
            for card in self.bottom_character_cards:
                card.update_layout()
        
        self.card_selector_background.update_layout()
        self.card_placeholder.update_layout()

        self.character_deck_button.update_layout()
        self.action_deck_button.update_layout()
        self.exit_button.update_layout()
        self.save_deck_button.update_layout()
        self.deck_button_placeholder.update_layout()
        self.rename_overlay.update_layout()
        self.rename_title.update_layout()
        self.rename_input.update_layout()
        self.rename_save_button.update_layout()
        self.rename_cancel_button.update_layout()
    
    def get_card_surface(self, name: str | None, card_type: Literal["char", "action"]) -> Surface:
        size: tuple[int, int] = (76, 130)
        surf: Surface = Surface(size)
        
        if name is None:
            # Empty Slot
            _ = surf.fill(color=(30, 40, 50))
            _ = pygame.draw.rect(surface=surf, color=(80, 90, 100), rect=surf.get_rect(), width=2)
        else:
            # Filled Card
            bg_color: tuple[int, int, int] = (195, 155, 100)
            _ = surf.fill(color=bg_color)
            _ = pygame.draw.rect(surface=surf, color=(50, 50, 50), rect=surf.get_rect(), width=3)
            font: Font = pygame.font.SysFont(name="arial", size=16, bold=True)
            text_surf: Surface = font.render(text=name.title(), antialias=True, color=(0, 0, 0))
            _ = surf.blit(source=text_surf, dest=text_surf.get_rect(center=(size[0]//2, size[1]//2)))
            
        return surf
    
    def get_action_card_surface(self, card_key: str) -> Surface:
        if card_key == "dummy":
            return self.get_card_surface(name=card_key, card_type="action")
        else:
            return GlobalHolder.resize_image(image=ActionCard.draw_action_card(card_key=card_key, die_needed=ACTION_DB[card_key]["cost"]["unaligned"]), size=((76, 130)))
    
    def get_character_card_surface(self, character_key: str, card_type: Literal["char", "action"]) -> Surface:
        """
        Loads a character card image based on the provided key and returns it as a Pygame Surface.
        """
        if character_key == "dummy":
            return self.get_card_surface(name=character_key, card_type=card_type)
        else:
            return GlobalHolder.resize_image(image=CharacterCard.draw_battle_card(character_key=character_key), size=((76, 130)))

        

        
    @override
    def draw(self) -> None:
        super().draw()
        self.exit_button.draw()
        if self.deck_sub_events["deck_list"]:
            for bg, char_surf, text_surf, menu in reversed(self.decks):
                bg.draw()
                if char_surf: char_surf.draw()
                if text_surf: text_surf.draw()
                if menu: menu.draw()
            
        if self.deck_sub_events["deck_preview_char"] or self.deck_sub_events["deck_preview_action"]:
            self.card_selector_background.draw()
            self.card_placeholder.draw()
            self.deck_button_placeholder.draw()
            self.action_deck_button.draw()
            self.character_deck_button.draw()
            self.save_deck_button.draw()

            if self.deck_sub_events["deck_preview_char"]:
                for card in self.top_character_cards:
                    card.draw()
                for card in self.bottom_character_cards:
                    card.draw()
            elif self.deck_sub_events["deck_preview_action"]:
                for card in self.top_action_cards:
                    card.draw()
                for card in self.bottom_action_cards:
                    card.draw()

        if self._rename_overlay_open():
            self.quit_game_overlay_background.draw()
            self.rename_overlay.draw()
            self.rename_title.draw()
            self.rename_input.draw()
            self.rename_save_button.draw()
            self.rename_cancel_button.draw()

    def draw_deck_card(self, cards: list[str]) -> Surface:
        """
        Takes a list of card image keys, loads them, and composites them 
        onto a single transparent Pygame Surface based on how many cards are present.
        """
        # Create a blank, transparent canvas large enough to hold the fanned cards
        canvas_width: int = 180
        canvas_height: int = 220
        canvas: Surface = Surface((canvas_width, canvas_height), pygame.SRCALPHA)
        
        num_cards: int = len(cards)
        if num_cards == 0:
            return canvas
            
        # Load the base images using your BasePage's load_image method
        loaded_images: list[Surface] = [GlobalHolder.resize_image(image=GlobalHolder.load_image(image_key=card), size=(76, 130)) for card in cards]
        if not loaded_images:
            return canvas
        # Base dimensions (assuming all cards are standard size, e.g., 80x120)
        center_x: int = canvas_width // 2
        center_y: int = canvas_height // 2
        
        if num_cards == 1:
            img: Surface = loaded_images[0]
            rect = img.get_rect(center=(center_x, center_y))
            _ = canvas.blit(source=img, dest=rect)
            
        elif num_cards == 2:
            # 2 Cards: Left card tilts left, right card tilts right[cite: 4]
            img0 = pygame.transform.rotate(surface=loaded_images[0], angle=12)
            img1 = pygame.transform.rotate(surface=loaded_images[1], angle=-12)
            
            rect0 = img0.get_rect(center=(center_x - 25, center_y))
            rect1 = img1.get_rect(center=(center_x + 25, center_y))
            
            # The right card overlaps the left card slightly[cite: 4]
            _ = canvas.blit(source=img0, dest=rect0)
            _ = canvas.blit(source=img1, dest=rect1)
            
        elif num_cards >= 3:
            # 3 Cards: Left/right cards tilt outwards, center card is straight[cite: 4]
            img0: Surface = pygame.transform.rotate(loaded_images[0], 25)
            img2: Surface = pygame.transform.rotate(loaded_images[2], -25)
            img1: Surface = loaded_images[1] # Center card is completely straight[cite: 4]
            
            rect0: Rect = img0.get_rect(center=(center_x - 45, center_y - 15))
            rect2: Rect = img2.get_rect(center=(center_x + 45, center_y - 15))
            rect1: Rect = img1.get_rect(center=(center_x, center_y))
            
            # Blit the side cards first so the straight center card overlaps them both[cite: 4]
            _ = canvas.blit(source=img0, dest=rect0)
            _ = canvas.blit(source=img2, dest=rect2)
            _ = canvas.blit(source=img1, dest=rect1)
            
        return canvas
