from django.urls import path
from . import views
 
urlpatterns = [
    # Kategorien + Terms (Admin)
    # path("categories/", views.CategoryListCreateView.as_view(), name="category-list"),
    # path("categories/<int:pk>/", views.CategoryDetailView.as_view(), name="category-detail"),
 
    #path("terms/", views.TermListCreateView.as_view(), name="term-list"),
    #path("terms/<int:pk>/", views.TermDetailView.as_view(), name="term-detail"),
 
    # Spiel-Endpoints
    path("join/", views.JoinView.as_view(), name="join"),
    path("current/", views.CurrentRoundView.as_view(), name="current-round"),
    path("submit/", views.SubmitView.as_view(), name="submit"),
    path("vote/", views.VoteView.as_view(), name="vote"),
    path("unknown/", views.UnknownTermsListView.as_view(), name="unknown-terms"),
    path("scoreboard/", views.ScoreboardView.as_view(), name="scoreboard"),
    path("me/score/", views.MyTotalScoreView.as_view(), name="my-total-score"),
 
    # Admin/Test
    # path("force-new-round/", views.ForceNewRoundView.as_view(), name="force-new-round"),
]

