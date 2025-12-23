"""
Poll Templates System
"""

POLL_TEMPLATES = {
    'which_better': {
        'name': 'Hangisi Daha İyi?',
        'category': 'comparison',
        'icon': '⚖️',
        'title_template': 'Hangisi daha iyi?',
        'options': ['Seçenek A', 'Seçenek B'],
        'description': 'İki seçenek arasında karşılaştırma yapın'
    },
    'yes_no': {
        'name': 'Evet/Hayır',
        'category': 'simple',
        'icon': '✅',
        'title_template': 'Sizce doğru mu?',
        'options': ['Evet', 'Hayır'],
        'description': 'Basit evet/hayır sorusu'
    },
    'agree_disagree': {
        'name': 'Katılıyor musunuz?',
        'category': 'opinion',
        'icon': '💭',
        'title_template': 'Bu fikre katılıyor musunuz?',
        'options': ['Katılıyorum', 'Katılmıyorum'],
        'description': 'Fikir ve görüş sorusu'
    },
    'this_or_that': {
        'name': 'Bu mu Şu mu?',
        'category': 'choice',
        'icon': '🤔',
        'title_template': 'Hangisini tercih edersiniz?',
        'options': ['Bu', 'Şu'],
        'description': 'İki seçenek arasında tercih'
    },
    'would_you_rather': {
        'name': 'Hangisini Tercih Ederdin?',
        'category': 'preference',
        'icon': '🎯',
        'title_template': 'Hangisini tercih ederdin?',
        'options': ['Birinci seçenek', 'İkinci seçenek'],
        'description': 'Tercih sorusu'
    },
    'true_false': {
        'name': 'Doğru/Yanlış',
        'category': 'quiz',
        'icon': '📝',
        'title_template': 'Bu bilgi doğru mu?',
        'options': ['Doğru', 'Yanlış'],
        'description': 'Bilgi testi sorusu'
    },
    'like_dislike': {
        'name': 'Beğendin mi?',
        'category': 'feedback',
        'icon': '👍',
        'title_template': 'Bunu beğendin mi?',
        'options': ['Beğendim', 'Beğenmedim'],
        'description': 'Beğeni sorusu'
    },
    'hot_or_not': {
        'name': 'İyi mi Kötü mü?',
        'category': 'rating',
        'icon': '🔥',
        'title_template': 'Bu nasıl?',
        'options': ['İyi', 'Kötü'],
        'description': 'Değerlendirme sorusu'
    },
}

TEMPLATE_CATEGORIES = {
    'comparison': 'Karşılaştırma',
    'simple': 'Basit',
    'opinion': 'Görüş',
    'choice': 'Tercih',
    'preference': 'Öncelik',
    'quiz': 'Test',
    'feedback': 'Geri Bildirim',
    'rating': 'Değerlendirme',
}


def get_template(template_id):
    """Get a specific template"""
    return POLL_TEMPLATES.get(template_id)


def get_templates_by_category(category=None):
    """Get templates by category"""
    if category:
        return {k: v for k, v in POLL_TEMPLATES.items() if v['category'] == category}
    return POLL_TEMPLATES


def get_all_categories():
    """Get all template categories"""
    return TEMPLATE_CATEGORIES
