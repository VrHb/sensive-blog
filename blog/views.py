from django.shortcuts import render
from django.db.models import Count
from blog.models import Comment, Post, Tag



def get_likes_count(post):
    return post.likes__count


def get_related_posts_count(tag):
    return tag.posts.count()


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.popular()],
        'first_tag_title': post.tags.popular().first().title,
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
        'tags': [serialize_tag(tag) for tag in post.tags.popular()],
        'first_tag_title': post.tags.all().first().title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts__count,
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
        .fetch_with_comments_count()
    
    most_fresh_posts = Post.objects.all().order_by(
        '-published_at'
    ).prefetch_related('author')[:5] 
    
    most_fresh_posts_ids = [post.id for post in most_fresh_posts]
    posts_with_comments = Post.objects.filter(
        id__in=most_fresh_posts_ids).annotate(comments_count=Count('comments')
    )
    ids_and_comments = posts_with_comments.values_list('id', 'comments_count')
    count_for_id = dict(ids_and_comments)
    for post in most_fresh_posts:
        post.comments_count = count_for_id[post.id]
    
    most_popular_tags = Tag.objects.popular()[:5].prefetch_related('posts')

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
    
    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': [serialize_comment(comment) for comment in post.comments.all()],
        'likes_amount': post.likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.popular()],
    }

    most_popular_tags = Tag.objects.popular()[:5]

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
    
    popular_tags = all_tags.popular()
    
    most_popular_tags = popular_tags[:5]

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
