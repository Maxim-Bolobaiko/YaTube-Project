from django.conf import settings
from django.core.paginator import Paginator


def paginator_func(post_list, request):
    paginator = Paginator(post_list, settings.PAGE_NUMBER_CONST)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
