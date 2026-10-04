from pathlib import Path




parent_dir: Path = Path(__file__).parent.parent

characters_images: dict[str, Path] = {
    "jean": parent_dir / "assets" / "images" / "characters" /"jean.jpg",
    "amber": parent_dir / "assets" / "images" / "characters" /"amber.jpg",
    "kaeya": parent_dir / "assets" / "images" / "characters" /"kaeya.jpg",
    "fischl": parent_dir / "assets" / "images" / "characters" /"fishcl.jpg",
}

action_cards_images: dict[str, Path] = {
    "magic_guide": parent_dir / "assets" / "images" / "action_cards" / "magic_guide.jpg",
    "raven_bow": parent_dir / "assets" / "images" / "action_cards" / "raven_bow.jpg",
    "white_iron_greatsword": parent_dir / "assets" / "images" / "action_cards" / "white_iron_greatsword.jpg",
    "white_tassel": parent_dir / "assets" / "images" / "action_cards" / "white_tassel.jpg",
    "travelers_handy_sword": parent_dir / "assets" / "images" / "action_cards" / "travelers_handy_sword.jpg",
    "exiles_circlet": parent_dir / "assets" / "images" / "action_cards" / "exiles_circlet.jpg",
    "broken_rimes_echo": parent_dir / "assets" / "images" / "action_cards" / "broken_rimes_echo.jpg",
    "wine_stained_tricorne": parent_dir / "assets" / "images" / "action_cards" / "wine_stained_tricorne.jpg",
    "witchs_scorching_hat": parent_dir / "assets" / "images" / "action_cards" / "witchs_scorching_hat.jpg",
    "thunder_summoners_crown": parent_dir / "assets" / "images" / "action_cards" / "thunder_summoners_crown.jpg",
    "viridescent_venerers_diadem": parent_dir / "assets" / "images" / "action_cards" / "viridescent_venerers_diadem.jpg",
    "mask_of_solitude_basalt": parent_dir / "assets" / "images" / "action_cards" / "mask_of_solitude_basalt.jpg",
    "laurel_coronet": parent_dir / "assets" / "images" / "action_cards" / "laurel_coronet.jpg",
    "dawn_winery": parent_dir / "assets" / "images" / "action_cards" / "dawn_winery.jpg",
    "favonious_cathedral": parent_dir / "assets" / "images" / "action_cards" / "favonious_cathedral.jpg",
    "paimon": parent_dir / "assets" / "images" / "action_cards" / "paimon.jpg",
    "sweet_madame": parent_dir / "assets" / "images" / "action_cards" / "sweet_madame.jpg",
    "mondstadt_hash_brown": parent_dir / "assets" / "images" / "action_cards" / "mondstadt_hash_brown.jpg",
    "minty_meat_rolls": parent_dir / "assets" / "images" / "action_cards" / "minty_meat_rolls.jpg",
}

images: dict[str, Path] = {
    "game_icon_64_64": parent_dir / "assets" / "images" / "game_icon_64_64.png",
    "cursor_pointer": parent_dir / "assets" / "images" / "cursor_pointer.png",
    "cursor_hand": parent_dir / "assets" / "images" / "cursor_hand.png",

    "background_image1" : parent_dir / "assets" / "images"/ "bg_1.png",
    "background_image2" : parent_dir / "assets" / "images"/ "bg_2.png",
    "background_image4" : parent_dir / "assets" / "images"/ "bg_4.png",

    "confirmation_overlay": parent_dir / "assets" / "images"/ "overlay_540_270.png",
    "overlay2": parent_dir / "assets" / "images" / "overlay_2.png",


    "button1": parent_dir / "assets" / "images" / "button_type1.png",
    "button2": parent_dir / "assets" / "images" / "button_type2.png",
    "button3": parent_dir / "assets" / "images" / "button_type3.png",
    "button1_outline": parent_dir / "assets" / "images" / "button_type1_outline.png",

    "text_input1": parent_dir / "assets" / "images" / "text_input1.png",
    "eye_open": parent_dir / "assets" / "images" / "eye_open.png",
    "eye_closed": parent_dir / "assets" / "images" / "eye_closed.png",


    "setting1": parent_dir / "assets" / "images" / "setting_icon_32_32.png",
    "setting_bg": parent_dir / "assets" / "images" / "setting_menu_bg.png",
    "dropdown_icon": parent_dir / "assets" / "images" / "dropdown_icon.png",

    "deck_box_active": parent_dir / "assets" / "images" / "deck_box_active.png",
    "locked_deck": parent_dir / "assets" / "images" / "locked_deck.png",
    "menu_dots": parent_dir / "assets" / "images" / "menu_dots.png",
    "card_selector": parent_dir / "assets" / "images" / "deck" / "card_selector.png",
    "card_placeholder": parent_dir / "assets" / "images" / "deck" / "card_placeholder.png",
    "deck_button_placeholder": parent_dir / "assets" / "images" / "deck" / "char_action_button_placeholder.png",
    "deck_button_character": parent_dir / "assets" / "images" / "deck" / "button_character.png",
    "deck_button_action": parent_dir / "assets" / "images" / "deck" / "button_action.png",

    "battle_bg1": parent_dir / "assets" / "images" / "battle" / "battle_bg1.png",
    "end_of_turn": parent_dir / "assets" / "images" / "battle" / "time_clock.png",
    "die_needed_action_card_placeholder": parent_dir / "assets" / "images" / "battle" / "die_needed_action_card_placeholder.png",
    "energy_unactive": parent_dir / "assets" / "images" / "battle" / "energy_unactive.png",
    "energy_active": parent_dir / "assets" / "images" / "battle" / "energy_active.png",
    "health_placeholder_character": parent_dir / "assets" / "images" / "battle" / "health_placeholder_character.png",
    "attack_placeholder": parent_dir / "assets" / "images" / "battle" / "attack_placeholder.png",
    "dice_number": parent_dir / "assets" / "images" / "battle" / "dice_number.png",
}

element_images: dict[str, Path] = {
    "element_pyro": parent_dir / "assets" / "images" / "battle" / "pyro.png",
    "element_hydro": parent_dir / "assets" / "images" / "battle" / "hydro.png",
    "element_anemo": parent_dir / "assets" / "images" / "battle" / "anemo.png",
    "element_electro": parent_dir / "assets" / "images" / "battle" / "electro.png",
    "element_dendro": parent_dir / "assets" / "images" / "battle" / "dendro.png",
    "element_cryo": parent_dir / "assets" / "images" / "battle" / "cryp#o.png",
    "element_geo": parent_dir / "assets" / "images" / "battle" / "geo.png",
}

images.update(element_images)
images.update(characters_images)
images.update(action_cards_images)


music: dict[str, Path] = {
    "theme_music_1": parent_dir / "assets" / "music" / "theme_music_1.mp3",
    "theme_music_2": parent_dir / "assets" / "music" / "theme_music_2.mp3",
}

sfx: dict[str, Path] = {
    "mouse_click_1": parent_dir / "assets" / "music" / "mouse_click_sfx1.mp3",
    "mouse_click2": parent_dir / "assets" / "music" / "mouse_click_sfx2.mp3",
    "keypress_click1": parent_dir / "assets" / "music" / "keypress_click_sfx1.mp3"
}

fonts: dict[str, Path] = {
    "Poppins": parent_dir / "assets" / "fonts" / "poppins.ttf",
    "Norwester": parent_dir / "assets" / "fonts" / "norwester.otf",
    "Hoyoverse": parent_dir / "assets" / "fonts" / "zh-cn.ttf",
    "Etna Free Font": parent_dir / "assets" / "fonts" / "etna-free-font.otf",
    #"norwester": parent_dir / "assets" / "fonts" / "norwester.otf"
}

