# assistant/urls.py
from django.urls import path
from .views import ChatView, ChatClassificationView, ChatSearchView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("classify/", ChatClassificationView.as_view(), name="chat_classify"),
    path("search/", ChatSearchView.as_view(), name="chat_search"),
]
