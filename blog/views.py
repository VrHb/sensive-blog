from django.shortcuts import render
from django.db.models import Count, Prefetch
from blog.models import Comment, Post, Tag



def get_likes_count(post):
    return post.likes__count


def get_related_posts_count(tag):
    return tag.posts_count


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all() \
            .annotate(posts_count=Count('posts'))
        ],
        'first_tag_title': post.tags.first().title,
    }


def serialize_post_optimized(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_optimized(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag_optimized(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def serialize_comment(comment):
    return {
        'text': comment.text,
        'published_at': comment.published_at,
        'author': comment.author.username,
    }


def index(request):
    most_popular_posts = Post.objects.popular() \
        .prefetch_related('author')[:5] \
        .prefetch_related(Prefetch('tags', queryset=Tag.objects.annotate(posts_count=Count('posts')))) \
        .fetch_with_comments_count()
    
    most_fresh_posts = Post.objects.order_by('-published_at') \
        .prefetch_related('author')[:5] \
        .prefetch_related(Prefetch('tags', queryset=Tag.objects.annotate(posts_count=Count('posts')))) \
        .fetch_with_comments_count()

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.annotate(
        likes_count=Count('likes'
    )).prefetch_related('tags').get(slug=slug)
    related_tags = post.tags.annotate(posts_count=Count('posts'))    
    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': [serialize_comment(comment) for comment in post.comments.all()],
        'likes_amount': post.likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = Tag.objects \
        .annotate(posts_count=Count('posts')) \
        .popular().prefetch_related('posts')[:5]

    most_popular_posts = Post.objects.popular() \
        .prefetch_related('author')[:5] \
        .fetch_with_comments_count()
    
    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    all_tags = Tag.objects.all().prefetch_related('posts')
    tag = all_tags.get(title=tag_title)
    
    most_popular_tags = Tag.objects \
        .annotate(posts_count=Count('posts')) \
        .popular().prefetch_related('posts')[:5]

    most_popular_posts = Post.objects.popular() \
        .prefetch_related('author')[:5] \
        .fetch_with_comments_count()

    related_posts = tag.posts.all()[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
