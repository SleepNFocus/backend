# 작성자: 한율
from typing import List, Union

from django.urls import URLPattern, URLResolver, path

from sleep_record.views import SleepRecordView

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path(
        "",
        SleepRecordView.as_view(),
        name="sleep_record",
    ),
]
