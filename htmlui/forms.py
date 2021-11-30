from django import forms

from bookmarks.models import Bookmark


class BookmarkForm(forms.Form):
    uri = forms.CharField(label='URI', widget=forms.TextInput(attrs={'size': 80}))
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 80}))
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 80}))

    @classmethod
    def from_bookmark(cls, bookmark: Bookmark):
        return cls({
            'uri': bookmark.resource.uri,
            'title': bookmark.resource.title,
            'tags': ' '.join(tag.value for tag in bookmark.resource.tags.all())
        })
