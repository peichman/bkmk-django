from django.shortcuts import render

from django.http import HttpResponse, JsonResponse

from .models import Bookmark


def annotation(bookmark):
    return {
        'type': 'Annotation',
        'motivation': 'bookmarking',
        'target': bookmark.resource.uri,
        'body': [{'type': 'TextualBody', 'purpose': 'tagging', 'value': t.value} for t in bookmark.resource.tags.all()],
        'created': bookmark.created,
        'modified': bookmark.modified
    }


def index(request):
    bookmarks = Bookmark.objects.all().order_by('-created')
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
