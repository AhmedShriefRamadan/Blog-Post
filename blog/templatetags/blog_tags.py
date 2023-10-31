from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe
import markdown

from ..models import Post,Category,CompanyProfile
from taggit.models import Tag

# to register the module
register = template.Library()



@register.simple_tag
def total_posts():
    return Post.published.count()


@register.inclusion_tag("blog/post/latest_posts.html")
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by("-publish")[:count]
    return {"latest_posts": latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count("comments")).order_by(
        "-total_comments"
    )[:count]


@register.filter(name="markdown")
def markdown_format(text):
    return mark_safe(markdown.markdown(text))




@register.simple_tag
def display_latest_posts(count=4):
    return Post.published.order_by('-publish')[:count]


@register.simple_tag
def show_categories(count=4):
    return Category.objects.exclude(image__isnull=True)[:count]


@register.simple_tag
def show_all_categories():
    return Category.objects.all()


@register.simple_tag
def show_all_tags():
    return Tag.objects.all()

@register.filter(name="is_company")
def is_company(user):
    return CompanyProfile.objects.filter(admin=user).exists()
