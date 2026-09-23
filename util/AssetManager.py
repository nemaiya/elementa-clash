from pathlib import Path




parent_dir: Path = Path(__file__).parent.parent


images: dict[str, Path] = {
    "game_icon_64_64": parent_dir / "assets" / "images" / "game_icon_64_64.png",
    "cursor_pointer": parent_dir / "assets" / "images" / "cursor_pointer.png",
    "cursor_hand": parent_dir / "assets" / "images" / "cursor_hand.png",

    "background_image1" : parent_dir / "assets" / "images"/ "bg_1.png",
    "background_image2" : parent_dir / "assets" / "images"/ "bg_2.png",

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
}

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
    "poppins": parent_dir / "assets" / "fonts" / "poppins.ttf",
    "norwester": parent_dir / "assets" / "fonts" / "norwester.otf",
    "hoyoverse": parent_dir / "assets" / "fonts" / "zh-cn.ttf",
    "etna_free_font": parent_dir / "assets" / "fonts" / "etna-free-font.otf",
    #"norwester": parent_dir / "assets" / "fonts" / "norwester.otf"
}

