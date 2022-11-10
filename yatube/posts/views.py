from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import paginator_func


@cache_page(5, key_prefix="index_page")
def index(request):
    template = "posts/index.html"
    post_list = Post.objects.all()
    context = {"page_obj": paginator_func(post_list, request)}
    return render(request, template, context)


def group_posts(request, slug):
    template = "posts/group_list.html"
    group = get_object_or_404(Group, slug=slug)
    group_post_list = group.posts.all()
    context = {
        "group": group,
        "page_obj": paginator_func(group_post_list, request),
    }
    return render(request, template, context)


def profile(request, username):
    template = "posts/profile.html"
    author = get_object_or_404(User, username=username)
    author_post = author.posts.all()
    posts_count = author_post.count()
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    context = {
        "page_obj": paginator_func(author_post, request),
        "author": author,
        "posts_count": posts_count,
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = get_object_or_404(Post, pk=post_id)
    posts_count = post.author.posts.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()

    liked = False

    if post.likes.filter(id=request.user.id).exists():
        liked = True

    context = {
        "post": post,
        "posts_count": posts_count,
        "form": form,
        "comments": comments,
        "likes_count": post.likes_count(),
        "post_is_liked": liked,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = "posts/create_post.html"
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", username=post.author)
    context = {
        "form": form,
        "is_edit": False,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = "posts/create_post.html"
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.user != post.author:
        return redirect("posts:post_detail", post.pk)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post.pk)
    context = {
        "form": form,
        "is_edit": True,
    }
    return render(request, template, context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user == post.author:
        post.delete()
    return redirect("posts:profile", username=post.author)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    post_comment_id = comment.post_id
    if request.user.username == comment.author.username:
        comment.delete()
    return redirect("posts:post_detail", post_comment_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    posts = Post.objects.filter(author__following__user=request.user)
    context = {"page_obj": paginator_func(posts, request)}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follower = request.user
    following = get_object_or_404(User, username=username)
    if follower != following:
        Follow.objects.get_or_create(user=follower, author=following)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    follower = request.user
    following = get_object_or_404(User, username=username)
    followed = Follow.objects.filter(user=follower, author=following)
    if followed.exists():
        followed.delete()
    return redirect("posts:profile", username=username)


@login_required
def post_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)

    return redirect("posts:post_detail", post_id=post_id)
