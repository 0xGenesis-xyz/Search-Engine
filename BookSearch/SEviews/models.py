from __future__ import unicode_literals
from django.db import models

# Create your models here.

class Books(models.Model):
    bid = models.IntegerField(primary_key=True, blank=True)#
    url = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)#
    subtitle = models.TextField(blank=True, null=True)#
    alt_title = models.TextField(blank=True, null=True)# ?
    author = models.TextField(blank=True, null=True)#
    translator = models.TextField(blank=True, null=True)# ?
    publisher = models.TextField(blank=True, null=True)#
    pubdate = models.TextField(blank=True, null=True)#
    binding = models.TextField(blank=True, null=True)#
    summary = models.TextField(blank=True, null=True)
    author_intro = models.TextField(blank=True, null=True)#×÷Õß¼ò½é
    catalog = models.TextField(blank=True, null=True)# ?
    rating = models.FloatField(blank=True, null=True)# ?
    numraters = models.IntegerField(db_column='numRaters', blank=True, null=True)  # Field name made lowercase.
    pages = models.TextField(blank=True, null=True)
    price = models.TextField(blank=True, null=True)#
    isbn13 = models.TextField(blank=True, null=True)
    isbn10 = models.TextField(blank=True, null=True)
    series = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    zjulib_url = models.TextField(blank=True, null=True)#
    class Meta:
        managed = False
        db_table = 'books'