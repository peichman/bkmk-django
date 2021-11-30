from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from bookmarks.models import Bookmark, Resource
from htmlui.forms import BookmarkForm


def get_title_or_uri(uri: str) -> str:
    response = requests.get(uri)
    if not response.ok:
        return uri
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.title.string or uri


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
                context = {
                    'form': BookmarkForm({
                        'uri': uri,
                        'title': get_title_or_uri(uri)
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
        resource, is_new = Resource.objects.get_or_create(uri=data['uri'])
        if is_new:
            now = datetime.now()
            bookmark = Bookmark.objects.create(resource=resource, created=now, modified=now)
            bookmark.update_and_save(data, now)
        else:
            bookmark = resource.bookmark
            bookmark.update_and_save(data)
        return HttpResponseRedirect(reverse('htmlui/bookmark_form.html', kwargs={'bookmark_id': bookmark.id}))


def edit_bookmark(request: HttpRequest, bookmark_id: int):
    bookmark = get_object_or_404(Bookmark, pk=bookmark_id)

    if request.method == 'GET':
        return render(request, 'htmlui/bookmark_form.html', context={'form': BookmarkForm.from_bookmark(bookmark)})
    elif request.method == 'POST':
        form = BookmarkForm(request.POST)

        if not form.is_valid():
            return render(request, 'htmlui/bookmark_form.html', context={'form': form})

        bookmark.update_and_save(form.cleaned_data)

        return HttpResponseRedirect(reverse('edit_bookmark', kwargs={'bookmark_id': bookmark.id}))
