from django import forms
from .models import Post, Comment
from django.views.generic import CreateView
from django.urls import reverse_lazy


class PostForm(forms.ModelForm):
    class Meta():
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка',
        }


class PostView(CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'
    succes_url = reverse_lazy('posts:posts_main')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
