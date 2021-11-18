from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:bookmark_id>', views.show_bookmark, name='bookmark')
]
