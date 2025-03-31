from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CommonPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'page': self.page.number,
            'size': self.page.paginator.per_page,
            'count': self.page.paginator.count,
            'data': data
        })

