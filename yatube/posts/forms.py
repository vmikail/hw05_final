from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Изображение',
        }
        help_texts = {
            'text': 'Напишите свой пост здесь',
            'group': 'Выберите нужную группу из списка',
            'image': 'Загрузите изображение',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        labels = {
            'text': 'Текст комментария',
        }
        help_texts = {
            'text': 'Напишите комментарий здесь',
        }
