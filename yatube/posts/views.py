from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import date
from django.views.decorators.cache import cache_page

from .forms import PostForm
from .models import Post, Group, User, CommentForm

ENTRIES = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related().all()
    paginator = Paginator(posts, ENTRIES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group')
    paginator = Paginator(posts, ENTRIES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Записи сообщества ' + str(group)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': title,
    }
    template = "posts/group_list.html"
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('author')
    paginator = Paginator(posts, ENTRIES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Профайл пользователя ' + str(user)
    context = {
        'user': user,
        'page_obj': page_obj,
        'title': title,
        'author': user,
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    posts_count = post.author.posts.count()
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    template = 'posts/post_detail.html'
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method != 'POST':
        return render(request, template, {'form': form})
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.pub_date = date.today()
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method != 'POST':
        return render(request, template, {'form': form})
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
        'post_id': post_id
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
