from django.core.paginator import Paginator
from core.constants import POSTS_PER_PAGE


def util_paginator(request, post_list):
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
