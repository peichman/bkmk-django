from cgi import parse_header
from urllib.parse import urlencode

from django.core.exceptions import BadRequest
from django.core.paginator import Paginator, Page
from django.http import JsonResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_safe

from .models import Bookmark

PAGE_SIZE = 10


class URL:
    def __init__(self, base, **params):
        self.base = base
        self.params = params

    def __str__(self):
        if self.params:
            return self.base + '?' + urlencode(self.params)
        else:
            return self.base

    def __add__(self, other):
        if isinstance(other, dict):
            return self.__class__(self.base, **{**self.params, **other})
        else:
            raise ValueError


class JsonLDResponse(JsonResponse):
    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if profile is not None:
            self.headers['Content-Type'] = f'application/ld+json; profile="{profile}"'
        else:
            self.headers['Content-Type'] = 'application/ld+json'


class AnnotationCollection:
    """
    Web Annotation Protocol-compliant view of the Bookmark model.
    """

    def __init__(self, request: HttpRequest):
        self.request = request
        self.paginator = Paginator(Bookmark.objects.all().order_by('-created'), PAGE_SIZE)

    def json(self):
        return {
            '@context': [
                'http://www.w3.org/ns/anno.jsonld',
                'http://www.w3.org/ns/ldp.jsonld'
            ],
            'type': [
                'BasicContainer',
                'AnnotationCollection'
            ],
            **self.metadata(),
            'first': self.page(1, standalone=False),
            'last': str(self.url + {'page': self.paginator.num_pages})
        }

    @property
    def url(self):
        return URL(self.request.build_absolute_uri(reverse('bookmarks_page')))

    def metadata(self) -> dict:
        return {
            'id': str(self.url),
            'total': len(self.paginator.object_list),
            # get the most recent modification timestamp
            'modified': Bookmark.objects.all().order_by('-modified')[0].modified,
            'label': 'Bookmarks Collection',
            'first': str(self.url + {'page': 1}),
            'last': str(self.url + {'page': self.paginator.num_pages})
        }

    def page(self, number: int, standalone: bool = True) -> dict:
        """
        Returns an Annotation Page as described in the Web Annotation Protocol.

        https://www.w3.org/TR/annotation-protocol/#annotation-pages
        """
        collection_metadata = {'partOf': self.metadata()} if standalone else {}
        context = {'@context': 'http://www.w3.org/ns/anno.jsonld'} if standalone else {}
        current_page = self.paginator.get_page(number)
        return {
            **context,
            'id': str(self.url + {'page': current_page.number}),
            'type': 'AnnotationPage',
            **collection_metadata,
            # adjust startIndex to start at 0 instead of 1
            'startIndex': current_page.start_index() - 1,
            **self.prev_next_links(current_page),
            **self.items(current_page)
        }

    def items(self, page: Page):
        def uri_for(bookmark):
            return self.request.build_absolute_uri(
                reverse('show_bookmark', kwargs={'bookmark_id': bookmark.id})
            )

        preference = self.request.GET.get('show', 'description')
        if preference == 'uri':
            return {'items': [uri_for(b) for b in page]}
        elif preference == 'description':
            return {'items': [{'id': uri_for(b), **annotation(b)} for b in page]}
        else:
            raise BadRequest(f'"{preference}" is not a valid "show" query parameter value')

    def prev_next_links(self, page: Page):
        links = {}
        if page.has_next():
            links['next'] = str(self.url + {'page': page.next_page_number()})
        if page.has_previous():
            links['prev'] = str(self.url + {'page': page.previous_page_number()})
        return links


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


def link_header(*links):
    return {
        'Link': ', '.join([f'<{target}>; rel="{rel}"' for rel, target in links])
    }


def show_parameter_value(request: HttpRequest):
    if 'Prefer' not in request.headers:
        # default to descriptions
        return 'description'

    preference, parameters = parse_header(request.headers['Prefer'].encode())
    if preference == 'return=representation':
        include_value = parameters.get('include', None)
        if include_value is None:
            # default to descriptions
            return 'description'

        includes = include_value.split(' ')
        if 'http://www.w3.org/ns/oa#PreferContainedIRIs' in includes:
            return 'uri'
        elif 'http://www.w3.org/ns/oa#PreferContainedDescriptions' in includes:
            return 'description'
        else:
            # default to descriptions
            return 'description'


@require_safe
def bookmarks_page(request: HttpRequest):
    collection = AnnotationCollection(request)
    if 'page' in request.GET:
        # single annotation page
        return JsonLDResponse(
            data=collection.page(int(request.GET['page'])),
            profile='http://www.w3.org/ns/anno.jsonld'
        )
    else:
        # main annotation collection
        return JsonLDResponse(
            data=collection.json(),
            profile='http://www.w3.org/ns/anno.jsonld',
            headers={
                **link_header(
                    ('type', 'http://www.w3.org/ns/ldp#BasicContainer'),
                    ('http://www.w3.org/ns/ldp#constrainedBy', 'http://www.w3.org/TR/annotation-protocol/')
                ),
                'Allow': 'GET, HEAD, OPTIONS'
            }
        )


@require_safe
def show_bookmark(request: HttpRequest, bookmark_id: int):
    bookmark = get_object_or_404(Bookmark, pk=bookmark_id)
    return JsonLDResponse(
        data={
            '@context': 'http://www.w3.org/ns/anno.jsonld',
            'id': request.build_absolute_uri(reverse('show_bookmark', kwargs={'bookmark_id': bookmark.id})),
            **annotation(bookmark)
        },
        profile='http://www.w3.org/ns/anno.jsonld',
        headers={
            **link_header(
                ('type', 'http://www.w3.org/ns/ldp#Resource'),
                ('type', 'http://www.w3.org/ns/oa#Annotation'),
            ),
            'Allow': 'GET, HEAD, OPTIONS'
        }
    )
