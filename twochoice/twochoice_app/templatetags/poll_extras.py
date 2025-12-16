from __future__ import annotations

from django import template

register = template.Library()


@register.simple_tag
def poll_total_votes(post):
    return post.votes.count()


@register.simple_tag
def poll_option_votes(option):
    return option.votes.count()


@register.simple_tag
def poll_percent(option, post):
    total = post.votes.count()
    if total <= 0:
        return 0
    votes = option.votes.count()
    return int(round((votes / total) * 100))


@register.simple_tag
def poll_max_percent(post):
    total = post.votes.count()
    if total <= 0:
        return 0

    percents = []
    for option in post.poll_options.all():
        votes = option.votes.count()
        percents.append((votes / total) * 100)

    return int(round(max(percents))) if percents else 0
