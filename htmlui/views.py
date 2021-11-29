from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from bookmarks.models import Bookmark, Resource, Tag
from htmlui.forms import BookmarkForm


def list_bookmarks(request: HttpRequest):
    if request.method == 'GET':
        if 'uri' in request.GET:
            uri = request.GET['uri']
            try:
                # redirect to the edit page for an existing bookmark
                bookmark = Bookmark.objects.get(resource__uri=uri)
                return HttpResponseRedirect(reverse('edit_bookmark', kwargs={'bookmark_id': bookmark.id}))
            except Bookmark.DoesNotExist:
                # show the form for a new bookmark
                soup = BeautifulSoup(requests.get(uri).text, 'html.parser')
                context = {
                    'form': BookmarkForm({
                        'uri': uri,
                        'title': soup.title.string
                    })
                }
                return render(request, 'htmlui/bookmark_form.html', context=context)

        bookmarks = Bookmark.objects.all()
        if 'tag' in request.GET:
            # do the intersection of all tags
            bookmarks = bookmarks.intersection(
                *(bookmarks.filter(resource__tags__value=tag) for tag in request.GET.getlist('tag'))
            )
        bookmarks = bookmarks.order_by('-created')
        paginator = Paginator(bookmarks, 10)
        context = {'paginator': paginator, 'bookmarks': paginator.get_page(1)}
        return render(request, 'htmlui/bookmarks_list.html', context=context)

    elif request.method == 'POST':
        form = BookmarkForm(request.POST)
        if not form.is_valid():
            return render(request, 'htmlui/bookmark_form.html', context={'form': form})

        data = form.cleaned_data
        resource, is_new = Resource.objects.get_or_create(uri=data['uri'], defaults={'title': data['title']})
        if is_new:
            now = datetime.now()
            bookmark = Bookmark.objects.create(resource=resource, created=now, modified=now)
            if data['tags']:
                for tag_value in data['tags'].split(' '):
                    tag, _ = Tag.objects.get_or_create(value=tag_value)
                    bookmark.resource.tags.add(tag)
        else:
            bookmark = resource.bookmark
            bookmark.update_fields(data)
        return HttpResponseRedirect(reverse('htmlui/bookmark_form.html', kwargs={'bookmark_id': bookmark.id}))


def edit_bookmark(request: HttpRequest, bookmark_id: int):
    bookmark = get_object_or_404(Bookmark, pk=bookmark_id)

    if request.method == 'GET':
        return render(request, 'htmlui/bookmark_form.html', context={'form': BookmarkForm.from_bookmark(bookmark)})
    elif request.method == 'POST':
        form = BookmarkForm(request.POST)

        if not form.is_valid():
            return render(request, 'htmlui/bookmark_form.html', context={'form': form})

        if bookmark.update_fields(form.cleaned_data):
            bookmark.modified = datetime.now()
            bookmark.resource.save()
            bookmark.save()

        return HttpResponseRedirect(reverse('edit_bookmark', kwargs={'bookmark_id': bookmark.id}))
