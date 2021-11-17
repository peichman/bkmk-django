from django.contrib import admin

from .models import Bookmark, Resource, Tag

admin.site.register(Tag)
admin.site.register(Resource)
admin.site.register(Bookmark)
