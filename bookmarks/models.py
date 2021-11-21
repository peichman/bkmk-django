from django.db import models


class Tag(models.Model):
    value = models.CharField(max_length=1024)

    def __str__(self):
        return self.value


class Resource(models.Model):
    uri = models.CharField(max_length=1024, unique=True)
    title = models.CharField(max_length=1024)
    tags = models.ManyToManyField(Tag, related_name='resources')

    def __str__(self):
        return self.uri


class Bookmark(models.Model):
    resource = models.ForeignKey(to=Resource, on_delete=models.CASCADE, related_name='bookmark')
    created = models.DateTimeField()
    modified = models.DateTimeField()
    deleted = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.resource.title

    def update_fields(self, data: dict) -> bool:
        changed = False
        if self.resource.title != data['title']:
            self.resource.title = data['title']
            changed = True
        if self.resource.uri != data['uri']:
            self.resource.uri = data['uri']
            changed = True
        if self.update_tags(data['tags']):
            changed = True
        return changed

    def update_tags(self, tag_string: str) -> bool:
        changed = False

        if tag_string:
            new_tag_values = set(tag_string.split(' '))
        else:
            new_tag_values = set()

        old_tag_values = set(tag.value for tag in self.resource.tags.all())
        added_tags = new_tag_values - old_tag_values
        removed_tags = old_tag_values - new_tag_values
        if len(added_tags) or len(removed_tags):
            changed = True
        for new_tag in added_tags:
            tag, _is_new = Tag.objects.get_or_create(value=new_tag)
            self.resource.tags.add(tag)
        for old_tag in removed_tags:
            self.resource.tags.remove(Tag.objects.get(value=old_tag))

        return changed
