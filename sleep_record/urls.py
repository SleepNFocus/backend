from typing import List, Union

from django.urls import URLPattern, URLResolver, path

from sleep_record.views import SleepRecordExistsAPIView, SleepRecordView

urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path(
        "",
        SleepRecordView.as_view(),
        name="sleep_record_create",
    ),
    path(
        "exist/",
        SleepRecordExistsAPIView.as_view(),
        name="sleep_record_exist",
    ),
]
