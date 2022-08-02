import django.contrib.auth.views as auth_views
from django.urls import path, include, reverse_lazy
from django.views import generic

from tapir.accounts import views

accounts_urlpatterns = [
    path(
        "", generic.RedirectView.as_view(pattern_name="accounts:user_me"), name="index"
    ),
    path("user/me/", views.UserMeView.as_view(), name="user_me"),
    path("user/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("user/<int:pk>/edit", views.UserUpdateView.as_view(), name="user_update"),
    path(
        "user/<int:pk>/send_welcome_email",
        views.send_user_welcome_email,
        name="send_user_welcome_email",
    ),
]

urlpatterns = [
    # Standard login/logout/password views should be un-namespaced because Django refers to them in a few places and
    # it's easier to do it like this than hunt down all the places and fix the references
    path("", include((accounts_urlpatterns, "accounts"))),
    path(
        "login/",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        auth_views.logout_then_login,
        name="logout",
    ),
]
