from pygame.surface import Surface


from pygame.font import Font


from pathlib import Path
from typing import Literal, TypeAlias

import pygame
from pygame.typing import ColorLike

from .AssetManager import fonts

Align: TypeAlias = Literal["left", "center", "right"]


class FontManager:
    def __init__(self, default_font: str | None = None) -> None:
        # Pygame's font subsystem must be initialized before creating fonts.
        if not pygame.font.get_init():
            _ = pygame.font.init()

        # Use the requested font when available, otherwise fall back to the first asset.
        self._font_key: str | None = default_font if default_font in fonts else (next(iter(fonts), None))
        # Cache fonts by their asset, size, and style settings to avoid recreating them.
        self._cached_fonts: dict[tuple[str | None, int, bool, bool, bool], Font] = {}

    def set_font(self, font_key: str) -> None:
        if font_key not in fonts:
            raise ValueError(f"Font '{font_key}' was not found in AssetManager.fonts")

        self._font_key = font_key

    def render(
        self, text: str, size: int, color: ColorLike = (255, 255, 255), max_width: int | None = None, align: Align = "left", 
        bold: bool = False, italic: bool = False, underline: bool = False, font_key: str | None = None,
    ) -> Surface:
        # Get the desired font from the built in method, which handles the retrieving process
        font: Font = self._get_font(size=size, bold=bold, italic=italic, underline=underline, font_key=font_key)

        # Wrap the input text to fit the requested width while preserving line breaks.
        lines: list[str] = self.get_text_lines_fitted_to_width(text, font, max_width)

        # Then render the texts
        surfaces: list[Surface] = [font.render(text=line, antialias=True, color=color) for line in lines]

        # Get the estimated height of the line
        # Buggy line: line_height: int = font.get_linesize()
        line_height: int = int(1.1 * font.get_linesize())

        # Ensure the output box is wide enough for the widest line, even when a single word exceeds max_width.
        width: int = max([max_width or 1] + [s.get_width() for s in surfaces])
        # The box height must cover every rendered line, while keeping at least the font height.
        height: int = max(line_height * len(surfaces), font.get_height())

        # Create a transparent surface to draw the text onto.
        box = Surface((width, height), pygame.SRCALPHA)

        # Map alignment to a horizontal offset multiplier: left = 0, center = 0.5, right = 1.
        align_mult: float = {"center": 0.5, "right": 1.0}.get(align, 0.0)

        # Blit each line at the correct x-position and stacked y-position.
        for i, surface in enumerate(surfaces):
            x: int = int((width - surface.get_width()) * align_mult)
            _ = box.blit(source=surface, dest=(x, i * line_height))

        
        return box

    def _get_font(self,size: int,bold: bool,italic: bool,underline: bool,font_key: str | None,) -> Font:
        # Determine which font to use: requested font or default font.
        key_name: str | None = font_key if font_key is not None else self._font_key
        # Create a cache key from font properties to identify unique font configurations.
        cache_key: tuple[str | None, int, bool, bool, bool] = (key_name, size, bold, italic, underline)

        # Check if this font configuration is already cached.
        cached: Font | None = self._cached_fonts.get(cache_key)
        if cached is not None:
            return cached

        # Retrieve the font file path and convert to string if it exists.
        font_path: Path | None = fonts.get(key_name) if key_name is not None else None
        filename: str | None = str(font_path) if font_path is not None and font_path.is_file() else None

        # Create a new pygame Font instance with the specified size and filename.
        font: Font = pygame.font.Font(filename=filename, size=size)
        # Apply style settings to the font.
        font.set_bold(bold)
        font.set_italic(italic)
        font.set_underline(underline)

        # Cache the font for future use.
        self._cached_fonts[cache_key] = font
        return font

    def get_text_lines_fitted_to_width(self, text: str, font: Font, max_width: int | None) -> list[str]:
        # If no width limit is provided, keep the original paragraph structure.
        if max_width is None:
            return text.split("\n") or [""]

        lines: list[str] = []
        # Process each paragraph separately so line breaks in the source text are preserved.
        for paragraph in text.split("\n"):
            current_line = ""
            # Split on spaces so words can be added one at a time while respecting max_width.
            for word in paragraph.split(" "):
                # Build the temp_str line with the next word, trimming any leading space.
                temp_str = f"{current_line} {word}".lstrip()

                # Keep adding words while the line still fits within the allowed width.
                if font.size(temp_str)[0] <= max_width:
                    current_line = temp_str
                else:
                    # Save the completed line before starting a new one.
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            # Add the final line for this paragraph after the loop completes.
            lines.append(current_line)

        return lines or [""]

    def split_word_by_pixel_width(self, word: str, font: Font, max_width: int) -> list[str]:
        """Breaks a single oversized word into smaller chunks that fit the pixel width."""
        if font.size(word)[0] <= max_width:
            return [word]

        chunks: list[str] = []
        current: str = ""
        for char in word:
            if current and font.size(current + char)[0] > max_width:
                chunks.append(current)
                current = char
            else:
                current += char

        return chunks + [current] if current else [word]

    def _wrap_text(self, text: str, font: Font, max_width: int | None) -> list[str]:
        paragraphs: list[str] = text.split(sep="\n")
        if max_width is None:
            return paragraphs if paragraphs else [""]

        lines: list[str] = []
        for paragraph in paragraphs:
            if paragraph == "":
                lines.append("")
                continue

            current: str = ""
            for word in paragraph.split(sep=" "):
                for piece in self._split_word(word=word, font=font, max_width=max_width):
                    temp_str: str = f"{current} {piece}".strip() if current else piece
                    if font.size(temp_str)[0] <= max_width:
                        current = temp_str
                    else:
                        if current:
                            lines.append(current)
                        current = piece

            if current:
                lines.append(current)

        return lines if lines else [""]

    def _split_word(self, word: str, font: Font, max_width: int) -> list[str]:
        if font.size(word)[0] <= max_width:
            return [word]

        pieces: list[str] = []
        current: str = ""
        for char in word:
            temp_str: str = current + char
            if current and font.size(temp_str)[0] > max_width:
                pieces.append(current)
                current = char
            else:
                current = temp_str

        if current:
            pieces.append(current)

        return pieces if pieces else [word]
