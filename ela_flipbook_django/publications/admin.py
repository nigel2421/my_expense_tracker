from django.contrib import admin
# publications/admin.py

from django.contrib import admin
from .models import Publication

admin.site.register(Publication)