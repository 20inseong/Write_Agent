from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")


def writer_setup(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "writer_setup.html",
        {"initial_block_index": 1},
    )


@require_GET
def add_block(request: HttpRequest) -> HttpResponse:
    try:
        block_index = int(request.GET.get("index", "2"))
    except ValueError:
        block_index = 2
    return render(
        request,
        "block_partial.html",
        {"block_index": block_index},
    )


def editor(request: HttpRequest) -> HttpResponse:
    return render(request, "editor.html")
