from django.urls import path
from .views import (
    CategoryListCreateView, CategoryDetailView,
    TermListCreateView, TermDetailView,
    JoinView, CurrentRoundView, SubmitView, VoteView, ScoreboardView, ForceNewRoundView, UnknownTermsListView
)

urlpatterns = [
    # Admin/CRUD
    path("categories/", CategoryListCreateView.as_view(), name="categories"),
    path("categories/<int:pk>/", CategoryDetailView.as_view(), name="category-detail"),
    path("terms/", TermListCreateView.as_view(), name="terms"),
    path("terms/<int:pk>/", TermDetailView.as_view(), name="term-detail"),

    # Spiel
    path("join/", JoinView.as_view(), name="join"),
    path("round/current/", CurrentRoundView.as_view(), name="round-current"),
    path("submit/", SubmitView.as_view(), name="submit"),
    path("vote/", VoteView.as_view(), name="vote"),
    path("scoreboard/", ScoreboardView.as_view(), name="scoreboard"),
    path("unknown-terms/", UnknownTermsListView.as_view(), name="unknown-terms"),

    # Admin/Test
    path("round/force-new/", ForceNewRoundView.as_view(), name="round-force-new"),
]
