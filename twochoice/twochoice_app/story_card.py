"""
Story formatında paylaşım kartı oluşturma modülü (1080x1920)
PIL ile dinamik görsel oluşturur
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import textwrap
from django.conf import settings
import os


def create_story_card(post, user_vote_option_id=None):
    """
    Story formatında paylaşım kartı oluşturur (1080x1920)
    
    Args:
        post: Post objesi
        user_vote_option_id: Kullanıcının seçtiği option ID (highlight için)
    
    Returns:
        BytesIO: PNG görsel
    """
    # Canvas boyutları (Instagram Story format)
    WIDTH = 1080
    HEIGHT = 1920
    
    # Premium Color Palette
    BG_COLOR = (250, 250, 252)  # Soft white
    PRIMARY_COLOR = (139, 92, 246)  # Purple
    SECONDARY_COLOR = (236, 72, 153)  # Pink
    ACCENT_COLOR = (59, 130, 246)  # Blue
    TEXT_COLOR = (15, 23, 42)  # Slate-900
    GRAY_COLOR = (100, 116, 139)  # Slate-500
    LIGHT_GRAY = (241, 245, 249)  # Slate-100
    
    # Canvas oluştur
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Font yükleme (fallback ile)
    try:
        title_font = ImageFont.truetype("arial.ttf", 68)
        option_font = ImageFont.truetype("arial.ttf", 52)
        percent_font = ImageFont.truetype("arialbd.ttf", 80)
        small_font = ImageFont.truetype("arial.ttf", 38)
        logo_font = ImageFont.truetype("arialbd.ttf", 52)
        tiny_font = ImageFont.truetype("arial.ttf", 32)
    except:
        title_font = ImageFont.load_default()
        option_font = ImageFont.load_default()
        percent_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        logo_font = ImageFont.load_default()
        tiny_font = ImageFont.load_default()
    
    # Premium gradient background (diagonal)
    for y in range(HEIGHT):
        # Purple to Pink gradient
        ratio = y / HEIGHT
        r = int(PRIMARY_COLOR[0] * (1 - ratio) + SECONDARY_COLOR[0] * ratio)
        g = int(PRIMARY_COLOR[1] * (1 - ratio) + SECONDARY_COLOR[1] * ratio)
        b = int(PRIMARY_COLOR[2] * (1 - ratio) + SECONDARY_COLOR[2] * ratio)
        alpha = int(20 * (1 - abs(ratio - 0.5) * 2))  # Fade in middle
        draw.rectangle([(0, y), (WIDTH, y + 1)], fill=(r, g, b, alpha))
    
    # White content card (rounded)
    card_margin = 60
    card_y_start = 140
    card_y_end = HEIGHT - 140
    draw.rounded_rectangle(
        [(card_margin, card_y_start), (WIDTH - card_margin, card_y_end)],
        radius=40,
        fill=(255, 255, 255)
    )
    
    # Subtle shadow effect
    shadow_offset = 8
    for i in range(shadow_offset):
        alpha = int(10 * (1 - i / shadow_offset))
        draw.rounded_rectangle(
            [(card_margin + i, card_y_start + i), (WIDTH - card_margin + i, card_y_end + i)],
            radius=40,
            outline=(0, 0, 0, alpha),
            width=2
        )
    
    # Logo badge (top)
    badge_y = 100
    badge_width = 280
    badge_height = 70
    badge_x = (WIDTH - badge_width) // 2
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
        radius=35,
        fill=PRIMARY_COLOR
    )
    draw.text((WIDTH // 2, badge_y + 35), "bilemedilema", font=logo_font, fill=(255, 255, 255), anchor="mm")
    
    # Başlık (wrapped) - centered in card
    title_y = 280
    title_text = post.title[:80]  # Max 80 karakter
    wrapped_title = textwrap.wrap(title_text, width=22)
    
    for i, line in enumerate(wrapped_title[:2]):  # Max 2 satır
        draw.text((WIDTH // 2, title_y + i * 85), line, font=title_font, fill=TEXT_COLOR, anchor="mm")
    
    # Divider line
    divider_y = title_y + 180
    divider_margin = 180
    draw.line(
        [(divider_margin, divider_y), (WIDTH - divider_margin, divider_y)],
        fill=LIGHT_GRAY,
        width=3
    )
    
    # Seçenekler ve yüzdeler
    options = list(post.poll_options.all())
    total_votes = post.votes.count()
    
    option_start_y = divider_y + 100
    option_spacing = 240
    
    for idx, option in enumerate(options[:4]):  # Max 4 seçenek göster
        y_pos = option_start_y + idx * option_spacing
        
        vote_count = option.votes.count()
        percent = int((vote_count / total_votes) * 100) if total_votes > 0 else 0
        
        # Kullanıcının seçimi mi?
        is_user_choice = (user_vote_option_id and option.id == user_vote_option_id)
        
        # Modern card design for each option
        card_x = 120
        card_width = WIDTH - 240
        card_height = 180
        card_y = y_pos - 90
        
        # Option card background
        card_color = (255, 255, 255) if not is_user_choice else LIGHT_GRAY
        draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_width, card_y + card_height)],
            radius=25,
            fill=card_color,
            outline=LIGHT_GRAY if not is_user_choice else PRIMARY_COLOR,
            width=4 if is_user_choice else 2
        )
        
        # Progress indicator (left side colored bar)
        if percent > 0:
            progress_width = int(card_width * (percent / 100))
            gradient_colors = [PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR]
            bar_color = gradient_colors[idx % 3]
            
            draw.rounded_rectangle(
                [(card_x, card_y), (card_x + progress_width, card_y + card_height)],
                radius=25,
                fill=(*bar_color, 40)  # Semi-transparent
            )
            
            # Colored left edge
            draw.rounded_rectangle(
                [(card_x, card_y), (card_x + 12, card_y + card_height)],
                radius=25,
                fill=bar_color
            )
        
        # Seçenek metni
        option_text = option.option_text[:28]  # Max 28 karakter
        text_x = card_x + 50
        text_y = y_pos - 20
        draw.text((text_x, text_y), option_text, font=option_font, fill=TEXT_COLOR, anchor="lm")
        
        # Vote count (small)
        vote_text = f"{vote_count} oy"
        draw.text((text_x, text_y + 60), vote_text, font=tiny_font, fill=GRAY_COLOR, anchor="lm")
        
        # Yüzde (büyük, sağda)
        percent_text = f"{percent}%"
        percent_x = card_x + card_width - 50
        draw.text((percent_x, y_pos), percent_text, font=percent_font, fill=PRIMARY_COLOR if is_user_choice else GRAY_COLOR, anchor="rm")
    
    # Footer section (in card)
    footer_y = card_y_end - 120
    
    # Total votes badge
    badge_width = 300
    badge_height = 60
    badge_x = (WIDTH - badge_width) // 2
    draw.rounded_rectangle(
        [(badge_x, footer_y), (badge_x + badge_width, footer_y + badge_height)],
        radius=30,
        fill=LIGHT_GRAY
    )
    
    footer_text = f"📊 {total_votes} kişi oy verdi"
    draw.text((WIDTH // 2, footer_y + 30), footer_text, font=small_font, fill=GRAY_COLOR, anchor="mm")
    
    # Bottom branding (outside card)
    url_y = HEIGHT - 80
    draw.text((WIDTH // 2, url_y), "bilemedilema.com", font=logo_font, fill=PRIMARY_COLOR, anchor="mm")
    
    # BytesIO'ya kaydet
    output = io.BytesIO()
    img.save(output, format='PNG', quality=95)
    output.seek(0)
    
    return output
