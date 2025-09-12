# publications/views.py

from django.shortcuts import render, get_object_or_404
from .models import Publication

def home_view(request):
    """
    This view gets all publications from the database and sends them
    to the home.html template.
    """
    publications = Publication.objects.all()
    context = {
        'publications': publications
    }
    return render(request, 'publications/home.html', context)


def publication_detail_view(request, pk):
    """
    This view gets a single publication by its unique ID (pk) and sends it
    to the publication_detail.html template.
    """
    publication = get_object_or_404(Publication, pk=pk)
    context = {
        'publication': publication
    }
    return render(request, 'publications/publication_detail.html', context)