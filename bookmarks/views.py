from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse, JsonResponse, HttpRequest

from .models import Bookmark


def annotation(bookmark):
    return {
        'type': 'Annotation',
        'motivation': 'bookmarking',
        'target': {
            'id': bookmark.resource.uri,
            'title': bookmark.resource.title
        },
        'body': [{'type': 'TextualBody', 'purpose': 'tagging', 'value': t.value} for t in bookmark.resource.tags.all()],
        'created': bookmark.created,
        'modified': bookmark.modified
    }


def index(request):
    bookmarks = Bookmark.objects.all().order_by('-created')[:10]
    collection = {
        '@context': [
            'http://www.w3.org/ns/anno.jsonld',
            'http://www.w3.org/ns/ldp.jsonld'
        ],
        'type': ['BasicContainer', 'AnnotationCollection'],
        'first': {
            'items': [annotation(b) for b in bookmarks]
        }
    }
    return JsonResponse(collection)


def show_bookmark(request: HttpRequest, bookmark_id: int):
    bookmark = get_object_or_404(Bookmark, pk=bookmark_id)
    return JsonResponse(annotation(bookmark))
