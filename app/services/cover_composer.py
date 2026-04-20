from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.models.schemas import CopyResult


def _theme_colors(theme: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    theme = theme or ""
    if "绿" in theme or "治愈" in theme:
        return (221, 239, 225), (93, 131, 116), (37, 73, 67)
    if "夜" in theme:
        return (35, 42, 67), (113, 132, 157), (244, 238, 220)
    if "书桌" in theme:
        return (231, 225, 211), (139, 111, 91), (62, 59, 52)
    return (225, 232, 238), (95, 121, 148), (42, 55, 70)


def _load_font(settings: Settings, size: int):
    from PIL import ImageFont

    font_candidates = []
    font_candidates.extend(settings.fonts_dir.glob("*.ttf"))
    font_candidates.extend(settings.fonts_dir.glob("*.otf"))
    font_candidates.extend(settings.fonts_dir.glob("*.ttc"))
    font_candidates.extend(
        [
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
            Path("C:/Windows/Fonts/simsun.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]
    )
    for candidate in font_candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _text_size(draw, text: str, font) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        width, _ = _text_size(draw, trial, font)
        if width <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def _draw_multiline(draw, xy: tuple[int, int], lines: list[str], font, fill, line_gap: int = 14) -> int:
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        _, height = _text_size(draw, line, font)
        y += height + line_gap
    return y


def _create_gradient(width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]):
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (width, height), top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    return image


def ensure_xulan_asset(settings: Settings) -> Path:
    from PIL import Image, ImageDraw

    path = Path(settings.xulan_asset_path)
    if path.exists():
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (640, 900), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((175, 80, 465, 370), fill=(246, 238, 224, 255), outline=(58, 87, 117, 255), width=8)
    draw.arc((105, 35, 535, 430), 200, 340, fill=(53, 88, 126, 255), width=45)
    draw.ellipse((235, 205, 270, 240), fill=(46, 56, 71, 255))
    draw.ellipse((370, 205, 405, 240), fill=(46, 56, 71, 255))
    draw.arc((280, 260, 360, 315), 20, 160, fill=(173, 93, 106, 255), width=6)
    draw.rounded_rectangle((130, 380, 510, 840), radius=80, fill=(92, 139, 156, 235))
    draw.rounded_rectangle((185, 465, 455, 665), radius=24, fill=(245, 241, 229, 255))
    draw.line((230, 525, 410, 525), fill=(95, 121, 148, 255), width=8)
    draw.line((230, 580, 390, 580), fill=(95, 121, 148, 255), width=8)
    font = _load_font(settings, 42)
    try:
        draw.text((225, 700), "Xulan", font=font, fill=(245, 241, 229, 255))
    except UnicodeError:
        draw.text((225, 700), "Xulan", fill=(245, 241, 229, 255))
    image.save(path)
    return path


def compose_cover(
    copy: CopyResult,
    output_path: Path,
    settings: Settings,
    cover_theme: str = "",
) -> Path:
    from PIL import Image, ImageDraw, ImageFilter

    width = settings.cover_width
    height = settings.cover_height
    top, bottom, ink = _theme_colors(cover_theme)
    image = _create_gradient(width, height, top, bottom).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    for offset in range(0, width, 84):
        draw.line((offset, 0, offset - width // 3, height), fill=(255, 255, 255, 18), width=2)
    draw.rounded_rectangle((68, 74, width - 68, height - 86), radius=34, outline=(255, 255, 255, 80), width=3)

    title_font = _load_font(settings, 76)
    subtitle_font = _load_font(settings, 38)
    tag_font = _load_font(settings, 30)
    small_font = _load_font(settings, 28)

    title_lines = _wrap_text(draw, copy.title, title_font, max_width=width - 210)
    y = _draw_multiline(draw, (105, 150), title_lines[:3], title_font, ink + (255,), line_gap=18)

    if copy.subtitle:
        subtitle_lines = _wrap_text(draw, copy.subtitle, subtitle_font, max_width=width - 250)
        y = _draw_multiline(draw, (108, y + 24), subtitle_lines[:2], subtitle_font, ink + (230,), line_gap=10)

    tag_text = copy.cover_text or "序蓝酱读书"
    tag_lines = _wrap_text(draw, tag_text, tag_font, max_width=width - 350)
    tag_y = min(y + 52, 560)
    tag_w = max((_text_size(draw, line, tag_font)[0] for line in tag_lines), default=260) + 58
    tag_h = len(tag_lines) * 46 + 28
    draw.rounded_rectangle((105, tag_y, 105 + tag_w, tag_y + tag_h), radius=22, fill=(255, 255, 255, 78))
    _draw_multiline(draw, (134, tag_y + 20), tag_lines[:2], tag_font, ink + (255,), line_gap=8)

    if copy.cover_keywords:
        keyword = " / ".join(copy.cover_keywords[:2])
        draw.text((108, height - 156), keyword[:32], font=small_font, fill=ink + (210,))

    asset_path = ensure_xulan_asset(settings)
    xulan = Image.open(asset_path).convert("RGBA")
    target_w = int(width * 0.43)
    ratio = target_w / xulan.width
    target_h = int(xulan.height * ratio)
    xulan = xulan.resize((target_w, target_h))

    shadow = Image.new("RGBA", xulan.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((60, target_h - 105, target_w - 20, target_h - 20), fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    x = width - target_w - 64
    y = height - target_h - 44
    image.alpha_composite(shadow, (x + 12, y + 18))
    image.alpha_composite(xulan, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path, quality=95)
    return output_path

