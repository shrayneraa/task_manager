import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Group, Post
from core.constants import ALL_PAGE

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_correct_template(self):
        templates_pages_names = {
            reverse('posts:group_list', kwargs=({'slug': f'{self.group.slug}'})
                    ): 'posts/group_list.html',
            reverse('posts:profile', kwargs=({'username': f'{self.user}'})
                    ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs=({'post_id': f'{self.post.id}'}
                                                 )): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs=({'post_id': f'{self.post.id}'})
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        context: list = []
        for i in range(13):
            context.append(Post(
                text=f'Тестовый текст {i}',
                group=self.group,
                author=self.user
            ))
        Post.objects.bulk_create(context)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), ALL_PAGE)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ContextViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_index_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image.name
        self.assertEqual(post_author_0, self.author.username)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, 'Тестовая группа')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_group_list_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        context_fields = {response.context['page_obj'][0].text:
                          'Тестовый пост',
                          response.context['page_obj'][0].group:
                          self.group,
                          response.context['page_obj'][0].author:
                          self.user.username,
                          response.context['page_obj'][0].image:
                          'posts/small.gif',
                          }
        for value, expected in context_fields.items():
            self.assertEqual(context_fields[value], expected)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text = {response.context['post'].text: 'Тестовый пост',
                     response.context['post'].group: self.group,
                     response.context['post'].author: self.user.username,
                     response.context['post'].image: 'posts/small.gif',
                     }
        for value, expected in post_text.items():
            self.assertEqual(post_text[value], expected)

    def test_post_profile_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        context_fields = {response.context['page_obj'][0].text:
                          'Тестовый пост',
                          response.context['page_obj'][0].group:
                          self.group,
                          response.context['page_obj'][0].author:
                          self.user.username,
                          response.context['page_obj'][0].image:
                          'posts/small.gif',
                          }
        for value, expected in context_fields.items():
            self.assertEqual(context_fields[value], expected)

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class CreatePostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = self.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_appears_on_pages_with_group(self):
        form_fields = {
            reverse('posts:index'): self.post,
            reverse('posts:profile', kwargs={'username': f'{self.user}'}
                    ): self.post,
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}
                    ): self.post,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)


class AddCommentAuthorizedUsercleaTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.user = self.author
        self.client = Client()
        self.client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_authorized_user_add_comment(self):
        self.authorized_client.post(f'/posts/{self.post.id}/comment/',
                                    {'text': "Комментарий"},
                                    follow=True)
        response = self.authorized_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.context['comments'][0].text, 'Комментарий')
        self.assertNotEqual(len(response.context['comments']), 0)


class PostPagesCacheTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='group',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.user = self.author
        self.client = Client()
        self.client.force_login(self.user)
        cache.clear()

    def test_index_page_is_cached(self):
        post = Post.objects.create(author=self.user,
                                   group=self.group,
                                   text='Тестируем кэширование'
                                   )
        reverse_index = reverse('posts:index')
        content_one = self.client.get(reverse_index).content
        post.delete()
        content_two = self.client.get(reverse_index).content
        self.assertEqual(content_one, content_two)
        cache.clear()
        content_three = self.client.get(reverse_index).content
        self.assertNotEqual(content_one, content_three)
