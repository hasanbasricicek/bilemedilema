# Content Filtering & Spam Detection

import re
from django.core.cache import cache

# Spam/Offensive word list (Turkish)
OFFENSIVE_WORDS = [
    'spam', 'reklam', 'link', 'tıkla', 'kazanç', 'para kazan',
    # Moderatörler buraya kelime ekleyebilir
]

# URL patterns
URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

def contains_spam(text):
    """Check if text contains spam keywords"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for offensive words
    for word in OFFENSIVE_WORDS:
        if word in text_lower:
            return True
    
    # Check for excessive URLs
    urls = URL_PATTERN.findall(text)
    if len(urls) > 2:
        return True
    
    # Check for excessive caps
    if len(text) > 20:
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if caps_ratio > 0.7:
            return True
    
    # Check for repeated characters
    if re.search(r'(.)\1{5,}', text):
        return True
    
    return False


def get_spam_score(text):
    """Calculate spam score (0-100)"""
    score = 0
    
    if not text:
        return 0
    
    text_lower = text.lower()
    
    # Offensive words (+20 each)
    for word in OFFENSIVE_WORDS:
        if word in text_lower:
            score += 20
    
    # URLs (+10 each, max 30)
    urls = URL_PATTERN.findall(text)
    score += min(len(urls) * 10, 30)
    
    # Excessive caps (+15)
    if len(text) > 20:
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if caps_ratio > 0.7:
            score += 15
    
    # Repeated characters (+10)
    if re.search(r'(.)\1{5,}', text):
        score += 10
    
    # Very short content (+5)
    if len(text.strip()) < 10:
        score += 5
    
    return min(score, 100)


def auto_moderate_content(content_type, content_id, text, author):
    """Automatically moderate content based on spam score"""
    from .models import Post, Comment, Report
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    spam_score = get_spam_score(text)
    
    # Auto-flag high spam score
    if spam_score >= 60:
        # Create automatic report
        system_user = User.objects.filter(is_superuser=True).first()
        if system_user:
            Report.objects.create(
                reporter=system_user,
                content_type=content_type,
                reported_post_id=content_id if content_type == 'post' else None,
                reported_comment_id=content_id if content_type == 'comment' else None,
                reason='spam',
                description=f'Otomatik spam tespiti (Skor: {spam_score})'
            )
        
        return True  # Flagged
    
    return False  # Not flagged


def add_offensive_word(word):
    """Add word to offensive list (admin only)"""
    if word and word.lower() not in OFFENSIVE_WORDS:
        OFFENSIVE_WORDS.append(word.lower())
        cache.set('offensive_words', OFFENSIVE_WORDS, timeout=None)
        return True
    return False


def remove_offensive_word(word):
    """Remove word from offensive list (admin only)"""
    if word and word.lower() in OFFENSIVE_WORDS:
        OFFENSIVE_WORDS.remove(word.lower())
        cache.set('offensive_words', OFFENSIVE_WORDS, timeout=None)
        return True
    return False


def get_offensive_words():
    """Get current offensive words list"""
    cached = cache.get('offensive_words')
    if cached:
        return cached
    return OFFENSIVE_WORDS
