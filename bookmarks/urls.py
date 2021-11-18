from django.urls import path

from . import views

urlpatterns = [
    path('', views.bookmarks_page, name='bookmarks_page'),
    path('<int:bookmark_id>', views.show_bookmark, name='show_bookmark')
]
