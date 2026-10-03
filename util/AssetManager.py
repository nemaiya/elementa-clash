from pathlib import Path




parent_dir: Path = Path(__file__).parent.parent

characters_images: dict[str, Path] = {
    "jean": parent_dir / "assets" / "images" / "characters" /"jean.jpg",
    "amber": parent_dir / "assets" / "images" / "characters" /"amber.jpg",
    "kaeya": parent_dir / "assets" / "images" / "characters" /"kaeya.jpg",
    "fishcl": parent_dir / "assets" / "images" / "characters" /"fishcl.jpg",
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
}

images.update(characters_images)


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

