from ast import pattern
from django.contrib import admin
from django.urls import path,include,re_path
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from blog.sitemaps import PostSitemap


sitemaps = {
    'posts':PostSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('blog.urls',namespace='blog')),
    path('sitemap.xml',sitemap,{'sitemaps':sitemaps},
        name='django.contirb.sitemaps.views.sitemap'),
    # To enforce django to serve then on deployment
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT}),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
#     pattern('',
#         (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
#         'document_root': settings.MEDIA_ROOT}))
