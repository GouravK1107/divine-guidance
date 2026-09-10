from django.urls import path

from guidance import views


urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "api/guidance/",
        views.guidance_api,
        name="guidance_api",
    ),
]