from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post


class PostSitemap(Sitemap):
    """Sitemap for published posts"""
    changefreq = "daily"
    priority = 0.8
    
    def items(self):
        return Post.objects.filter(status='p', is_deleted=False).order_by('-created_at')
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('post_detail', args=[obj.pk])


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.5
    changefreq = 'weekly'
    
    def items(self):
        return ['home']
    
    def location(self, item):
        return reverse(item)
