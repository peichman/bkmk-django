from django.urls import path

from . import views

urlpatterns = [
    path('', views.list_bookmarks, name='list_bookmarks'),
    path('<int:bookmark_id>', views.edit_bookmark, name='edit_bookmark')
]
