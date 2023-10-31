# this code creates a custom sitemap class for your Django project's blog posts. It specifies how often the pages change (changefreq), their priority (priority), which posts to include (items), and how to determine the last modification date (lastmod) for each post in the sitemap. This custom sitemap class is then used to generate the sitemap XML that provides information to search engines about your blog posts.


from django.contrib.sitemaps import Sitemap

from .models import Post


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Post.published.all()
    
    def lastmod(self, obj):
        return obj.updated

