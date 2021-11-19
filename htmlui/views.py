from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from bookmarks.models import Bookmark


def list_bookmarks(request: HttpRequest):
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


def edit_bookmark(_request: HttpRequest, bookmark_id: int):
    return HttpResponse('TODO: edit ' + str(bookmark_id))
