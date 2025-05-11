from rest_framework.pagination import PageNumberPagination
from django.conf import settings

class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = settings.PAGE_SIZE_QUERY_PARAM
    page_size = settings.REST_FRAMEWORK.get('PAGE_SIZE', 6)
    max_page_size = 100