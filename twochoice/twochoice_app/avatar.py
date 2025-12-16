from __future__ import annotations

import json
from typing import Any, Dict, Optional

from django.utils.html import escape


AVATAR_MODE_CHOICES = [
    ('initial', 'Baş Harf'),
    ('preset', 'Hazır Avatar'),
    ('custom', 'Özel Avatar'),
]

PRESET_CHOICES = [
    ('mono_1', 'Mono 1'),
    ('mono_2', 'Mono 2'),
    ('mono_3', 'Mono 3'),
    ('robot_1', 'Robot 1'),
    ('cat_1', 'Kedi 1'),
]


_ALLOWED_BG = {
    'sand': '#F5F5F0',
    'gray': '#BFBFBF',
    'black': '#000000',
    'slate': '#666A73',
    'blue': '#0B5275',
    'rust': '#B33F00',
    'mint': '#A7F3D0',
    'lavender': '#DDD6FE',
    'peach': '#FED7AA',
}

_ALLOWED_SKIN = {
    'light': '#F2D6C1',
    'tan': '#E6BFA2',
    'brown': '#C98E6A',
    'dark': '#8E5B3E',
    'pale': '#FFE4D6',
    'olive': '#D4B896',
    'none': '#FFFFFF',
}

_ALLOWED_HAIR = {'none', 'short', 'bob', 'mohawk', 'long', 'curly', 'bun', 'ponytail', 'braids', 'pixie', 'afro', 'wavy', 'sidepart'}
_ALLOWED_HAIR_COLOR = {'black': '#111827', 'brown': '#78350F', 'blonde': '#FCD34D', 'red': '#DC2626', 'gray': '#9CA3AF'}
_ALLOWED_EYES = {'dot', 'happy', 'wink', 'closed', 'surprised'}
_ALLOWED_MOUTH = {'smile', 'open', 'flat', 'grin', 'sad'}
_ALLOWED_FACIAL_HAIR = {'none', 'beard', 'mustache', 'goatee'}
_ALLOWED_FACE_SHAPE = {'default', 'oval', 'square', 'round'}
_ALLOWED_CAT_TYPE = {'orange', 'black', 'white', 'gray', 'calico', 'tuxedo'}
_ALLOWED_CAT_EYE_COLOR = {'green': '#58D68D', 'blue': '#3B82F6', 'yellow': '#FCD34D', 'orange': '#F97316', 'gray': '#9CA3AF'}
_ALLOWED_ROBOT_TYPE = {'classic', 'round', 'visor'}
_ALLOWED_ACC = {'none', 'glasses', 'earring', 'sunglasses', 'beanie', 'brow_piercing', 'nose_piercing'}


_PRESET_CONFIGS: Dict[str, Dict[str, Any]] = {
    'mono_1': {'bg': 'sand', 'skin': 'none', 'hair': 'short', 'eyes': 'happy', 'mouth': 'smile', 'acc': 'none'},
    'mono_2': {'bg': 'gray', 'skin': 'none', 'hair': 'bob', 'eyes': 'dot', 'mouth': 'flat', 'acc': 'glasses'},
    'mono_3': {'bg': 'slate', 'skin': 'none', 'hair': 'mohawk', 'eyes': 'wink', 'mouth': 'smile', 'acc': 'none'},
    'robot_1': {'bg': 'sand', 'skin': 'none', 'hair': 'none', 'eyes': 'dot', 'mouth': 'open', 'acc': 'none', 'robot': True, 'robot_type': 'classic'},
    'cat_1': {'bg': 'sand', 'skin': 'none', 'hair': 'none', 'eyes': 'happy', 'mouth': 'smile', 'acc': 'none', 'cat': True},
}


def sanitize_avatar_config(config: Any) -> Dict[str, Any]:
    if not isinstance(config, dict):
        return {}

    bg = config.get('bg')
    skin = config.get('skin')
    hair = config.get('hair')
    eyes = config.get('eyes')
    mouth = config.get('mouth')
    acc = config.get('acc')

    safe: Dict[str, Any] = {}

    if bg in _ALLOWED_BG:
        safe['bg'] = bg
    if skin in _ALLOWED_SKIN:
        safe['skin'] = skin
    if hair in _ALLOWED_HAIR:
        safe['hair'] = hair
    
    hair_color = config.get('hair_color')
    if hair_color in _ALLOWED_HAIR_COLOR:
        safe['hair_color'] = hair_color
    
    face_shape = config.get('face_shape')
    if face_shape in _ALLOWED_FACE_SHAPE:
        safe['face_shape'] = face_shape
    
    cat_type = config.get('cat_type')
    if cat_type in _ALLOWED_CAT_TYPE:
        safe['cat_type'] = cat_type
    
    cat_eye_color = config.get('cat_eye_color')
    if cat_eye_color in _ALLOWED_CAT_EYE_COLOR:
        safe['cat_eye_color'] = cat_eye_color

    robot_type = config.get('robot_type')
    if robot_type in _ALLOWED_ROBOT_TYPE:
        safe['robot_type'] = robot_type
    
    if eyes in _ALLOWED_EYES:
        safe['eyes'] = eyes
    if mouth in _ALLOWED_MOUTH:
        safe['mouth'] = mouth
    
    facial_hair = config.get('facial_hair')
    if facial_hair in _ALLOWED_FACIAL_HAIR:
        safe['facial_hair'] = facial_hair
    
    if acc in _ALLOWED_ACC:
        safe['acc'] = acc

    # optional flags
    if config.get('robot') is True:
        safe['robot'] = True
    if config.get('cat') is True:
        safe['cat'] = True

    # Normalize: cat/robot are mutually exclusive and ignore human-only fields.
    if safe.get('robot') is True:
        safe.pop('cat', None)
        safe.pop('cat_type', None)
        safe.pop('cat_eye_color', None)
        safe['skin'] = 'none'
        safe['face_shape'] = 'default'
        safe['hair'] = 'none'
        safe.pop('hair_color', None)
        safe['facial_hair'] = 'none'
        if safe.get('robot_type') not in _ALLOWED_ROBOT_TYPE:
            safe['robot_type'] = 'classic'
    elif safe.get('cat') is True:
        safe.pop('robot', None)
        safe.pop('robot_type', None)
        safe['skin'] = 'none'
        safe['face_shape'] = 'default'
        safe['hair'] = 'none'
        safe.pop('hair_color', None)
        safe['facial_hair'] = 'none'

    return safe


def parse_avatar_config_json(value: str) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        raw = json.loads(value)
    except Exception:
        return {}
    return sanitize_avatar_config(raw)


def _svg_header(size: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        'viewBox="0 0 64 64" fill="none" role="img" aria-hidden="true">'
    )


def render_initial_avatar_svg(initial: str, size: int = 40, bg_hex: str = '#666A73') -> str:
    ch = (initial or '?').strip()[:1]
    ch = escape(ch.upper())
    return (
        _svg_header(size)
        + f'<rect x="0" y="0" width="64" height="64" rx="32" fill="{bg_hex}"/>'
        + f'<text x="32" y="40" text-anchor="middle" font-family="ui-sans-serif, system-ui" '
        + 'font-size="26" font-weight="700" fill="#FFFFFF">'
        + f'{ch}</text>'
        + '</svg>'
    )


def _draw_face(config: Dict[str, Any]) -> str:
    bg = _ALLOWED_BG.get(config.get('bg', 'sand'), '#F5F5F0')
    skin = _ALLOWED_SKIN.get(config.get('skin', 'none'), '#FFFFFF')

    parts = [
        f'<rect x="0" y="0" width="64" height="64" rx="32" fill="{bg}"/>'
    ]

    if config.get('robot'):
        robot_type = config.get('robot_type', 'classic')

        if robot_type == 'round':
            parts.append('<line x1="32" y1="10" x2="32" y2="16" stroke="#111827" stroke-width="2" stroke-linecap="round"/>')
            parts.append('<circle cx="32" cy="9" r="3" fill="#F97316" stroke="#111827" stroke-width="2"/>')
            parts.append('<circle cx="32" cy="36" r="18" fill="#E5E7EB" stroke="#111827" stroke-width="2"/>')
            parts.append('<rect x="18" y="30" width="28" height="10" rx="5" fill="#93C5FD" stroke="#111827" stroke-width="2"/>')
            parts.append('<circle cx="14" cy="36" r="3" fill="#9CA3AF" stroke="#111827" stroke-width="2"/>')
            parts.append('<circle cx="50" cy="36" r="3" fill="#9CA3AF" stroke="#111827" stroke-width="2"/>')
        elif robot_type == 'visor':
            parts.append('<rect x="12" y="18" width="40" height="34" rx="12" fill="#E5E7EB" stroke="#111827" stroke-width="2"/>')
            parts.append('<rect x="16" y="28" width="32" height="12" rx="6" fill="#111827"/>')
            parts.append('<rect x="18" y="30" width="28" height="8" rx="4" fill="#22C55E" opacity="0.85"/>')
            parts.append('<circle cx="18" cy="24" r="2" fill="#F97316"/>')
            parts.append('<circle cx="46" cy="24" r="2" fill="#3B82F6"/>')
        else:
            parts.append('<rect x="14" y="18" width="36" height="32" rx="8" fill="#E5E7EB" stroke="#111827" stroke-width="2"/>')
            parts.append('<rect x="18" y="28" width="28" height="10" rx="5" fill="#BFDBFE" stroke="#111827" stroke-width="2"/>')
            parts.append('<circle cx="20" cy="34" r="1.5" fill="#111827"/>')
            parts.append('<circle cx="44" cy="34" r="1.5" fill="#111827"/>')
    elif config.get('cat'):
        # Cat with different colors
        cat_type = config.get('cat_type', 'orange')
        cat_colors = {
            'orange': ('#FF9500', '#FFB84D'),
            'black': ('#111827', '#374151'),
            'white': ('#F9FAFB', '#E5E7EB'),
            'gray': ('#6B7280', '#9CA3AF'),
            'calico': ('#FF9500', '#FFFFFF'),
            'tuxedo': ('#6B7280', '#F9FAFB')
        }
        main_color, accent_color = cat_colors.get(cat_type, ('#FF9500', '#FFB84D'))
        
        # Cute cat head with ears
        parts.append(f'<path d="M18 28 L22 16 L28 24 Z" fill="{main_color}" stroke="#111827" stroke-width="1.5"/>')  # Left ear
        parts.append(f'<path d="M46 28 L42 16 L36 24 Z" fill="{main_color}" stroke="#111827" stroke-width="1.5"/>')  # Right ear
        parts.append(f'<circle cx="32" cy="36" r="18" fill="{main_color}" stroke="#111827" stroke-width="2"/>')  # Head
        # Inner ear details
        parts.append(f'<path d="M20 24 L23 18 L26 24" fill="{accent_color}" stroke="none"/>')  # Left inner ear
        parts.append(f'<path d="M44 24 L41 18 L38 24" fill="{accent_color}" stroke="none"/>')  # Right inner ear
        # Cheeks
        parts.append(f'<circle cx="20" cy="40" r="4" fill="{accent_color}" opacity="0.6"/>')  # Left cheek
        parts.append(f'<circle cx="44" cy="40" r="4" fill="{accent_color}" opacity="0.6"/>')  # Right cheek
        # Nose
        parts.append('<path d="M32 38 L30 42 L34 42 Z" fill="#111827"/>')  # Nose triangle
        
        # Calico pattern (spots)
        if cat_type == 'calico':
            parts.append('<circle cx="24" cy="32" r="3" fill="#FFFFFF"/>')
            parts.append('<circle cx="40" cy="44" r="4" fill="#FFFFFF"/>')

        if cat_type == 'tuxedo':
            parts.append(f'<ellipse cx="32" cy="44" rx="11" ry="7" fill="{accent_color}" opacity="0.95"/>')
            parts.append(f'<ellipse cx="32" cy="50" rx="9" ry="6" fill="{accent_color}" opacity="0.95"/>')
    else:
        # Different face shapes
        face_shape = config.get('face_shape', 'default')
        if face_shape == 'oval':
            parts.append(f'<ellipse cx="32" cy="34" rx="14" ry="17" fill="{skin}" stroke="#111827" stroke-width="2"/>')
        elif face_shape == 'square':
            parts.append(f'<rect x="16" y="18" width="32" height="32" rx="4" fill="{skin}" stroke="#111827" stroke-width="2"/>')
        elif face_shape == 'round':
            parts.append(f'<circle cx="32" cy="34" r="18" fill="{skin}" stroke="#111827" stroke-width="2"/>')
        else:  # default
            parts.append(f'<circle cx="32" cy="34" r="16" fill="{skin}" stroke="#111827" stroke-width="2"/>')

    return ''.join(parts)


def _draw_hair(config: Dict[str, Any]) -> str:
    if config.get('robot') or config.get('cat'):
        return ''

    hair = config.get('hair', 'none')
    hair_color = _ALLOWED_HAIR_COLOR.get(config.get('hair_color', 'black'), '#111827')
    face_shape = config.get('face_shape', 'default')
    
    if hair == 'none':
        return ''
    
    # Adjust hair positioning based on face shape
    if face_shape == 'oval':
        # Oval face: narrower, adjust hair to fit
        if hair == 'short':
            return f'<path d="M20 30 C22 22, 42 22, 44 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
        if hair == 'bob':
            return f'<path d="M20 32 C22 20, 42 20, 44 32" stroke="{hair_color}" stroke-width="8" stroke-linecap="round"/>'
        if hair == 'long':
            return f'<path d="M20 30 C20 40, 20 48, 22 52 M44 30 C44 40, 44 48, 42 52" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
        if hair == 'curly':
            return f'<path d="M22 28 Q20 24, 24 22 Q22 20, 26 20 Q30 18, 32 18 Q34 18, 38 20 Q42 20, 40 22 Q44 24, 42 28" fill="{hair_color}"/>'
        if hair == 'pixie':
            return f'<path d="M22 28 C24 22, 30 18, 32 18 C34 18, 40 22, 42 28" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
        if hair == 'wavy':
            return f'<path d="M20 30 Q22 24, 26 26 Q30 28, 32 22 Q34 28, 38 26 Q42 24, 44 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round" fill="none"/>'
        if hair == 'sidepart':
            return f'<path d="M22 28 C24 22, 30 18, 32 18 M32 18 C34 18, 40 22, 42 28" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
    elif face_shape == 'square':
        # Square face: adjust to corners
        if hair == 'short':
            return f'<path d="M16 26 L18 20 L46 20 L48 26" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
        if hair == 'bob':
            return f'<path d="M16 30 L18 18 L46 18 L48 30" stroke="{hair_color}" stroke-width="8" stroke-linecap="round"/>'
        if hair == 'long':
            return f'<path d="M16 28 L16 48 M48 28 L48 48" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
        if hair == 'curly':
            return f'<path d="M18 26 Q16 22, 20 20 Q18 18, 22 18 Q28 16, 32 16 Q36 16, 42 18 Q46 18, 44 20 Q48 22, 46 26" fill="{hair_color}"/>'
        if hair == 'pixie':
            return f'<path d="M18 26 C20 20, 28 16, 32 16 C36 16, 44 20, 46 26" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
        if hair == 'wavy':
            return f'<path d="M16 28 Q18 22, 22 24 Q28 26, 32 20 Q36 26, 42 24 Q46 22, 48 28" stroke="{hair_color}" stroke-width="6" stroke-linecap="round" fill="none"/>'
        if hair == 'sidepart':
            return f'<path d="M18 26 C20 20, 28 16, 32 16 M32 16 C36 16, 44 20, 46 26" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
    elif face_shape == 'round':
        # Round face: wider, fuller hair
        if hair == 'short':
            return f'<path d="M16 32 C18 20, 46 20, 48 32" stroke="{hair_color}" stroke-width="7" stroke-linecap="round"/>'
        if hair == 'bob':
            return f'<path d="M16 34 C18 18, 46 18, 48 34" stroke="{hair_color}" stroke-width="9" stroke-linecap="round"/>'
        if hair == 'long':
            return f'<path d="M16 32 C16 42, 16 50, 18 54 M48 32 C48 42, 48 50, 46 54" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
        if hair == 'curly':
            return f'<path d="M18 30 Q16 26, 20 24 Q18 22, 22 22 Q28 20, 32 20 Q36 20, 42 22 Q46 22, 44 24 Q48 26, 46 30" fill="{hair_color}"/>'
        if hair == 'pixie':
            return f'<path d="M18 30 C20 24, 28 20, 32 20 C36 20, 44 24, 46 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
        if hair == 'wavy':
            return f'<path d="M16 32 Q18 24, 22 26 Q28 28, 32 22 Q36 28, 42 26 Q46 24, 48 32" stroke="{hair_color}" stroke-width="7" stroke-linecap="round" fill="none"/>'
        if hair == 'sidepart':
            return f'<path d="M18 30 C20 22, 28 20, 32 20 M32 20 C36 20, 44 22, 46 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
    
    # Default face shape - all remaining styles
    if hair == 'short':
        return f'<path d="M18 30 C20 20, 44 20, 46 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
    if hair == 'bob':
        return f'<path d="M18 32 C20 18, 44 18, 46 32" stroke="{hair_color}" stroke-width="8" stroke-linecap="round"/>'
    if hair == 'long':
        return f'<path d="M18 30 C18 40, 18 48, 20 52 M46 30 C46 40, 46 48, 44 52" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
    if hair == 'curly':
        return f'<path d="M20 28 Q18 24, 22 22 Q20 20, 24 20 Q28 18, 32 18 Q36 18, 40 20 Q44 20, 42 22 Q46 24, 44 28" fill="{hair_color}"/>'
    if hair == 'pixie':
        return f'<path d="M20 28 C22 22, 28 18, 32 18 C36 18, 42 22, 44 28" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
    if hair == 'wavy':
        return f'<path d="M18 30 Q20 22, 24 24 Q28 26, 32 20 Q36 26, 40 24 Q44 22, 46 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round" fill="none"/>'
    if hair == 'sidepart':
        return f'<path d="M20 28 C22 20, 28 18, 32 18 M32 18 C36 18, 42 20, 44 28" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
    
    # Universal styles (work for all face shapes)
    if hair == 'mohawk':
        return f'<path d="M32 16 L32 30" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>'
    if hair == 'bun':
        # Adjust bun position based on face shape
        if face_shape == 'square':
            return f'<circle cx="32" cy="16" r="6" fill="{hair_color}"/>'
        elif face_shape == 'round':
            return f'<circle cx="32" cy="20" r="7" fill="{hair_color}"/>'
        elif face_shape == 'oval':
            return f'<circle cx="32" cy="17" r="5" fill="{hair_color}"/>'
        return f'<circle cx="32" cy="18" r="6" fill="{hair_color}"/>'
    if hair == 'ponytail':
        # Adjust ponytail based on face shape
        if face_shape == 'square':
            return f'<path d="M32 16 C32 16, 32 10, 34 6" stroke="{hair_color}" stroke-width="7" stroke-linecap="round"/>' \
                   f'<circle cx="34" cy="6" r="5" fill="{hair_color}"/>'
        elif face_shape == 'round':
            return f'<path d="M32 20 C32 20, 32 14, 34 10" stroke="{hair_color}" stroke-width="7" stroke-linecap="round"/>' \
                   f'<circle cx="34" cy="10" r="5" fill="{hair_color}"/>'
        elif face_shape == 'oval':
            return f'<path d="M32 17 C32 17, 32 11, 34 7" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>' \
                   f'<circle cx="34" cy="7" r="4" fill="{hair_color}"/>'
        return f'<path d="M32 18 C32 18, 32 12, 34 8" stroke="{hair_color}" stroke-width="6" stroke-linecap="round"/>' \
               f'<circle cx="34" cy="8" r="4" fill="{hair_color}"/>'
    if hair == 'braids':
        # Adjust braids based on face shape
        if face_shape == 'square':
            return f'<path d="M18 28 C16 32, 14 36, 14 40" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>' \
                   f'<path d="M46 28 C48 32, 50 36, 50 40" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
        elif face_shape == 'round':
            return f'<path d="M16 32 C14 36, 12 40, 12 44" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>' \
                   f'<path d="M48 32 C50 36, 52 40, 52 44" stroke="{hair_color}" stroke-width="5" stroke-linecap="round"/>'
        elif face_shape == 'oval':
            return f'<path d="M22 30 C20 34, 18 38, 18 42" stroke="{hair_color}" stroke-width="4" stroke-linecap="round"/>' \
                   f'<path d="M42 30 C44 34, 46 38, 46 42" stroke="{hair_color}" stroke-width="4" stroke-linecap="round"/>'
        return f'<path d="M20 30 C18 34, 16 38, 16 42" stroke="{hair_color}" stroke-width="4" stroke-linecap="round"/>' \
               f'<path d="M44 30 C46 34, 48 38, 48 42" stroke="{hair_color}" stroke-width="4" stroke-linecap="round"/>'
    if hair == 'afro':
        # Adjust afro size based on face shape - smaller to not cover face
        if face_shape == 'square':
            return f'<circle cx="32" cy="18" r="12" fill="{hair_color}"/>'
        elif face_shape == 'round':
            return f'<circle cx="32" cy="20" r="13" fill="{hair_color}"/>'
        elif face_shape == 'oval':
            return f'<ellipse cx="32" cy="18" rx="10" ry="12" fill="{hair_color}"/>'
        return f'<circle cx="32" cy="18" r="11" fill="{hair_color}"/>'  # Smaller and higher
    return ''


def _draw_eyes(config: Dict[str, Any]) -> str:
    if config.get('cat'):
        # Cute cat eyes with vertical pupils - customizable eye color
        eye_color = _ALLOWED_CAT_EYE_COLOR.get(config.get('cat_eye_color', 'green'), '#58D68D')
        return f'<ellipse cx="26" cy="34" rx="3" ry="5" fill="{eye_color}"/>' \
               '<ellipse cx="26" cy="34" rx="1" ry="4" fill="#111827"/>' \
               f'<ellipse cx="38" cy="34" rx="3" ry="5" fill="{eye_color}"/>' \
               '<ellipse cx="38" cy="34" rx="1" ry="4" fill="#111827"/>' \
               '<circle cx="25" cy="32" r="0.8" fill="#FFFFFF"/>' \
               '<circle cx="37" cy="32" r="0.8" fill="#FFFFFF"/>'  # Eye shine

    eyes = config.get('eyes', 'dot')
    if eyes == 'dot':
        return '<circle cx="26" cy="34" r="2" fill="#111827"/><circle cx="38" cy="34" r="2" fill="#111827"/>'
    if eyes == 'happy':
        return '<path d="M24 34 C25 32, 27 32, 28 34" stroke="#111827" stroke-width="2" stroke-linecap="round"/>' \
               '<path d="M36 34 C37 32, 39 32, 40 34" stroke="#111827" stroke-width="2" stroke-linecap="round"/>'
    if eyes == 'wink':
        return '<path d="M24 34 C25 32, 27 32, 28 34" stroke="#111827" stroke-width="2" stroke-linecap="round"/>' \
               '<path d="M36 34 L40 34" stroke="#111827" stroke-width="2" stroke-linecap="round"/>'
    if eyes == 'closed':
        return '<path d="M24 34 L28 34" stroke="#111827" stroke-width="2" stroke-linecap="round"/>' \
               '<path d="M36 34 L40 34" stroke="#111827" stroke-width="2" stroke-linecap="round"/>'
    if eyes == 'surprised':
        return '<circle cx="26" cy="34" r="3" fill="#111827"/><circle cx="38" cy="34" r="3" fill="#111827"/>'
    return ''


def _draw_mouth(config: Dict[str, Any]) -> str:
    if config.get('cat'):
        # Cat mouth with whiskers
        mouth = '<path d="M32 42 L32 45" stroke="#111827" stroke-width="1.5" stroke-linecap="round"/>'  # Vertical line
        mouth += '<path d="M28 44 C30 43, 30 43, 32 42" stroke="#111827" stroke-width="1.5" stroke-linecap="round" fill="none"/>'  # Left smile
        mouth += '<path d="M36 44 C34 43, 34 43, 32 42" stroke="#111827" stroke-width="1.5" stroke-linecap="round" fill="none"/>'  # Right smile
        # Whiskers
        mouth += '<path d="M14 36 L22 36" stroke="#111827" stroke-width="1" stroke-linecap="round"/>'  # Left whisker top
        mouth += '<path d="M14 38 L22 38" stroke="#111827" stroke-width="1" stroke-linecap="round"/>'  # Left whisker mid
        mouth += '<path d="M14 40 L22 40" stroke="#111827" stroke-width="1" stroke-linecap="round"/>'  # Left whisker bottom
        mouth += '<path d="M50 36 L42 36" stroke="#111827" stroke-width="1" stroke-linecap="round"/>'  # Right whisker top
        mouth += '<path d="M50 38 L42 38" stroke="#111827" stroke-width="1" stroke-linecap="round"/>'  # Right whisker mid
        mouth += '<path d="M50 40 L42 40" stroke="#111827" stroke-width="1" stroke-linecap="round"/>'  # Right whisker bottom
        return mouth

    mouth = config.get('mouth', 'smile')
    if mouth == 'smile':
        return '<path d="M26 42 C28 46, 36 46, 38 42" stroke="#111827" stroke-width="2" stroke-linecap="round"/>'
    if mouth == 'open':
        return '<circle cx="32" cy="44" r="3" fill="#111827"/>'
    if mouth == 'flat':
        return '<path d="M26 44 L38 44" stroke="#111827" stroke-width="2" stroke-linecap="round"/>'
    if mouth == 'grin':
        return '<path d="M26 42 C28 48, 36 48, 38 42" stroke="#111827" stroke-width="2" stroke-linecap="round" fill="none"/>' \
               '<path d="M28 44 L36 44" stroke="#111827" stroke-width="1"/>'
    if mouth == 'sad':
        return '<path d="M26 46 C28 44, 36 44, 38 46" stroke="#111827" stroke-width="2" stroke-linecap="round"/>'
    return ''


def _draw_facial_hair(config: Dict[str, Any]) -> str:
    if config.get('robot') or config.get('cat'):
        return ''
    
    facial_hair = config.get('facial_hair', 'none')
    hair_color = _ALLOWED_HAIR_COLOR.get(config.get('hair_color', 'black'), '#111827')
    face_shape = config.get('face_shape', 'default')
    
    if facial_hair == 'none':
        return ''
    
    # Adapt facial hair to face shape
    if face_shape == 'oval':
        if facial_hair == 'beard':
            return f'<path d="M24 42 C24 47, 28 49, 32 49 C36 49, 40 47, 40 42" fill="{hair_color}"/>'
        if facial_hair == 'mustache':
            return f'<path d="M26 40 C28 38, 30 38, 32 40 C34 38, 36 38, 38 40" stroke="{hair_color}" stroke-width="2.5" stroke-linecap="round" fill="none"/>'
        if facial_hair == 'goatee':
            return f'<path d="M30 45 C30 48, 32 50, 34 48 C34 45, 32 45, 30 45" fill="{hair_color}"/>'
    elif face_shape == 'square':
        if facial_hair == 'beard':
            return f'<path d="M18 40 L18 48 L46 48 L46 40" fill="{hair_color}"/>'
        if facial_hair == 'mustache':
            return f'<path d="M22 38 C24 36, 30 36, 32 38 C34 36, 40 36, 42 38" stroke="{hair_color}" stroke-width="3.5" stroke-linecap="round" fill="none"/>'
        if facial_hair == 'goatee':
            return f'<rect x="28" y="44" width="8" height="6" rx="2" fill="{hair_color}"/>'
    elif face_shape == 'round':
        if facial_hair == 'beard':
            return f'<path d="M20 42 C20 50, 26 52, 32 52 C38 52, 44 50, 44 42" fill="{hair_color}"/>'
        if facial_hair == 'mustache':
            return f'<path d="M22 40 C24 38, 30 38, 32 40 C34 38, 40 38, 42 40" stroke="{hair_color}" stroke-width="3.5" stroke-linecap="round" fill="none"/>'
        if facial_hair == 'goatee':
            return f'<path d="M29 46 C29 51, 32 53, 35 51 C35 46, 32 46, 29 46" fill="{hair_color}"/>'
    
    # Default face shape
    if facial_hair == 'beard':
        return f'<path d="M22 42 C22 48, 26 50, 32 50 C38 50, 42 48, 42 42" fill="{hair_color}"/>'
    if facial_hair == 'mustache':
        return f'<path d="M24 40 C26 38, 30 38, 32 40 C34 38, 38 38, 40 40" stroke="{hair_color}" stroke-width="3" stroke-linecap="round" fill="none"/>'
    if facial_hair == 'goatee':
        return f'<path d="M30 46 C30 50, 32 52, 34 50 C34 46, 32 46, 30 46" fill="{hair_color}"/>'
    return ''


def _draw_accessory(config: Dict[str, Any]) -> str:
    acc = config.get('acc', 'none')
    if acc == 'glasses':
        return '<rect x="21" y="31" width="10" height="7" rx="3" stroke="#111827" stroke-width="2"/>' \
               '<rect x="33" y="31" width="10" height="7" rx="3" stroke="#111827" stroke-width="2"/>' \
               '<path d="M31 34 L33 34" stroke="#111827" stroke-width="2"/>'
    if acc == 'sunglasses':
        return '<rect x="21" y="31" width="10" height="7" rx="3" fill="#111827"/>' \
               '<rect x="33" y="31" width="10" height="7" rx="3" fill="#111827"/>' \
               '<path d="M31 34 L33 34" stroke="#111827" stroke-width="2"/>'
    if acc == 'beanie':
        return '<path d="M18 26 C20 16, 44 16, 46 26" fill="#111827"/>' \
               '<path d="M18 26 C20 20, 44 20, 46 26" fill="#374151"/>' \
               '<rect x="18" y="26" width="28" height="6" rx="3" fill="#111827"/>'
    if acc == 'brow_piercing':
        return '<circle cx="24" cy="30" r="2.2" fill="none" stroke="#BFBFBF" stroke-width="1.5"/>' \
               '<circle cx="24" cy="30" r="0.8" fill="#BFBFBF"/>'
    if acc == 'nose_piercing':
        return '<circle cx="32" cy="41" r="1.4" fill="#BFBFBF"/>' \
               '<circle cx="34" cy="41" r="1.4" fill="#BFBFBF"/>'
    if acc == 'earring':
        return '<circle cx="46" cy="40" r="2" fill="#B33F00"/>'
    return ''


def render_avatar_svg_from_config(config: Dict[str, Any], size: int = 40) -> str:
    safe = sanitize_avatar_config(config)

    # defaults
    safe.setdefault('bg', 'sand')
    safe.setdefault('skin', 'none')
    safe.setdefault('hair', 'none')
    safe.setdefault('eyes', 'dot')
    safe.setdefault('mouth', 'smile')
    safe.setdefault('acc', 'none')

    body = _draw_face(safe) + _draw_hair(safe) + _draw_eyes(safe) + _draw_mouth(safe) + _draw_facial_hair(safe) + _draw_accessory(safe)
    return _svg_header(size) + body + '</svg>'


def resolve_profile_avatar_config(profile: Any) -> Optional[Dict[str, Any]]:
    if not profile:
        return None

    mode = getattr(profile, 'avatar_mode', 'initial') or 'initial'
    if mode == 'custom':
        cfg = getattr(profile, 'avatar_config', None)
        if isinstance(cfg, dict) and cfg:
            return sanitize_avatar_config(cfg)
        return None

    if mode == 'preset':
        preset = getattr(profile, 'avatar_preset', '') or ''
        cfg = _PRESET_CONFIGS.get(preset)
        if cfg:
            return sanitize_avatar_config(cfg)
        return None

    return None


def get_preset_choices() -> list[tuple[str, str]]:
    return PRESET_CHOICES


def get_preset_config(preset_key: str) -> Optional[Dict[str, Any]]:
    cfg = _PRESET_CONFIGS.get(preset_key)
    if not cfg:
        return None
    return sanitize_avatar_config(cfg)


def get_preset_svg(preset_key: str, size: int = 48) -> str:
    cfg = _PRESET_CONFIGS.get(preset_key)
    if not cfg:
        return render_initial_avatar_svg('?', size=size)
    return render_avatar_svg_from_config(cfg, size=size)
