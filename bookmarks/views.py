from urllib.parse import urlencode

from django.core.paginator import Paginator, Page
from django.http import JsonResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_safe

from .models import Bookmark

PAGE_SIZE = 10


class JsonLDResponse(JsonResponse):
    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if profile is not None:
            self.headers['Content-Type'] = f'application/ld+json; profile="{profile}"'
        else:
            self.headers['Content-Type'] = 'application/ld+json'


def prev_next_links(url, current_page: Page):
    links = {}
    if current_page.has_next():
        links['next'] = url + '?' + urlencode({'page': current_page.next_page_number()})
    if current_page.has_previous():
        links['prev'] = url + '?' + urlencode({'page': current_page.previous_page_number()})
    return links


def collection_metadata(paginator: Paginator):
    return {
        'total': len(paginator.object_list),
        # get the most recent modification timestamp
        'modified': Bookmark.objects.all().order_by('-modified')[0].modified,
    }


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


def annotation_page(current_page: Page, request: HttpRequest):
    url = request.build_absolute_uri(reverse('bookmarks_page'))
    return {
        '@context': 'http://www.w3.org/ns/anno.jsonld',
        'id': url + '?' + urlencode({'page': current_page.number}),
        'type': 'AnnotationPage',
        'partOf': {
            'id': url,
            **collection_metadata(current_page.paginator)
        },
        # adjust startIndex to start at 0 instead of 1
        'startIndex': current_page.start_index() - 1,
        **prev_next_links(url, current_page),
        **items(current_page, request)
    }


def items(current_page: Page, request: HttpRequest):
    return {
        'items': [{
            'id': request.build_absolute_uri(reverse('show_bookmark', kwargs={'bookmark_id': b.id})),
            **annotation(b)
        } for b in current_page]
    }


def annotation_collection(paginator: Paginator, request: HttpRequest):
    return {
        '@context': [
            'http://www.w3.org/ns/anno.jsonld',
            'http://www.w3.org/ns/ldp.jsonld'
        ],
        'type': ['BasicContainer', 'AnnotationCollection'],
        **collection_metadata(paginator),
        'first': annotation_page(paginator.get_page(1), request),
        'last': request.build_absolute_uri(reverse('bookmarks_page')) + '?' + urlencode({'page': paginator.num_pages})
    }


@require_safe
def bookmarks_page(request: HttpRequest):
    paginator = Paginator(Bookmark.objects.all().order_by('-created'), PAGE_SIZE)
    if 'page' in request.GET:
        # single annotation page
        current_page = paginator.get_page(int(request.GET['page']))
        return JsonLDResponse(
            annotation_page(current_page, request),
            profile='http://www.w3.org/ns/anno.jsonld'
        )
    else:
        # main annotation collection
        return JsonLDResponse(
            annotation_collection(paginator, request),
            profile='http://www.w3.org/ns/anno.jsonld',
            headers={
                **link_header(
                    ('type', 'http://www.w3.org/ns/ldp#BasicContainer'),
                    ('http://www.w3.org/ns/ldp#constrainedBy', 'http://www.w3.org/TR/annotation-protocol/')
                ),
                'Allow': 'GET, HEAD, OPTIONS'
            }
        )


def link_header(*links):
    return {
        'Link': ', '.join([f'<{target}>; rel="{rel}"' for rel, target in links])
    }


@require_safe
def show_bookmark(request: HttpRequest, bookmark_id: int):
    bookmark = get_object_or_404(Bookmark, pk=bookmark_id)
    return JsonLDResponse(
        {
            'id': request.build_absolute_uri(reverse('show_bookmark', kwargs={'bookmark_id': bookmark.id})),
            **annotation(bookmark)
        },
        profile='http://www.w3.org/ns/anno.jsonld'
    )
