from django import forms


class BookmarkForm(forms.Form):
    uri = forms.CharField(label='URI')
    title = forms.CharField()
    tags = forms.CharField(required=False)
