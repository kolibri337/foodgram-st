from rest_framework.pagination import PageNumberPagination

class AccountPagination(PageNumberPagination):
    """Класс пагинации для списка пользователей"""
    
    default_page_size = 6
    page_size = default_page_size
    max_page_size = 50
    page_query_param = 'page'
    page_size_query_param = 'per_page'
    
    def get_page_size(self, request):
        if self.page_size_query_param in request.query_params:
            try:
                return min(
                    int(request.query_params[self.page_size_query_param]),
                    self.max_page_size
                )
            except (ValueError, TypeError):
                pass
        return self.page_size
