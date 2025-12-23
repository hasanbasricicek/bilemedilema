"""Küfür ve argo filtresi"""
import re

# Türkçe küfür ve argo kelimeler listesi
PROFANITY_WORDS = [
    'amk', 'amq', 'aq', 'mk', 'mq', 'oç', 'orospu', 'piç', 'sik', 'yarrak',
    'göt', 'am', 'amcık', 'taşak', 'siktir', 'bok', 'kaka', 'pezevenk',
    'kahpe', 'sürtük', 'fahişe', 'ibne', 'top', 'eşek', 'salak', 'gerizekalı',
    'mal', 'aptal', 'ahmak', 'dangalak', 'geri zekalı', 'beyinsiz', 'salak',
]

def contains_profanity(text):
    """Metinde küfür var mı kontrol et"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Kelime bazlı kontrol
    for word in PROFANITY_WORDS:
        # Tam kelime eşleşmesi
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            return True
        
        # Karakterler arası boşluk/nokta ile yazılmış (a.m.k, a m k gibi)
        spaced_pattern = r'\b' + r'[\s\.\-_]*'.join(re.escape(c) for c in word) + r'\b'
        if re.search(spaced_pattern, text_lower):
            return True
    
    return False


def filter_profanity(text):
    """Küfürlü kelimeleri yıldızla değiştir"""
    if not text:
        return text
    
    filtered_text = text
    text_lower = text.lower()
    
    for word in PROFANITY_WORDS:
        # Tam kelime eşleşmesi
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = list(re.finditer(pattern, text_lower))
        
        for match in reversed(matches):
            start, end = match.span()
            original = filtered_text[start:end]
            replacement = original[0] + '*' * (len(original) - 1)
            filtered_text = filtered_text[:start] + replacement + filtered_text[end:]
    
    return filtered_text


def get_profanity_warning():
    """Küfür uyarı mesajı"""
    return "Yorumunuz küfür veya uygunsuz içerik içeriyor. Lütfen düzenleyin."
