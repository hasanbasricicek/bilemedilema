from __future__ import annotations

from django import template
from django.utils.safestring import mark_safe

from twochoice_app.avatar import (
    get_preset_svg,
    render_avatar_svg_from_config,
    render_initial_avatar_svg,
    resolve_profile_avatar_config,
)

register = template.Library()


@register.simple_tag
def avatar(user, size=40):
    try:
        size_int = int(size)
    except Exception:
        size_int = 40

    profile = None
    try:
        profile = getattr(user, 'profile', None)
    except Exception:
        profile = None

    cfg = resolve_profile_avatar_config(profile)
    if cfg:
        return mark_safe(render_avatar_svg_from_config(cfg, size=size_int))

    initial = ''
    try:
        initial = (getattr(user, 'username', '') or '')[:1]
    except Exception:
        initial = ''

    return mark_safe(render_initial_avatar_svg(initial, size=size_int))


@register.simple_tag
def avatar_preset_svg(preset_key, size=56):
    try:
        size_int = int(size)
    except Exception:
        size_int = 56
    return mark_safe(get_preset_svg(str(preset_key), size=size_int))
