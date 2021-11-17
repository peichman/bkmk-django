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
