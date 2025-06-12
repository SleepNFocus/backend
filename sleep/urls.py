# 작성자: 한율
from typing import List, Union

from django.urls import URLPattern, URLResolver

urlpatterns: List[Union[URLPattern, URLResolver]] = []
