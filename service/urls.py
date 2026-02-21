from django.urls import path

from .views import ChallengeMarathonAPIView, MarathonDetailAPIView, MarathonDayAPIView, MarathonDayUserAPIView, StatisticUserMarathonAPIView, MarathonAdminView

urlpatterns = [
    path("marathon/", ChallengeMarathonAPIView.as_view()),
    path("marathon/<int:pk>/", MarathonDetailAPIView.as_view()),
    path("marathon/<int:marathon_id>/daily/", MarathonDayAPIView.as_view()),
    path("marathon/<int:marathon_id>/day/", MarathonDayUserAPIView.as_view()),
    path("marathon/<int:marathon_id>/statistics/", StatisticUserMarathonAPIView.as_view()),
    path("marathon/<int:marathon_id>/statistics/user/<int:user_id>/", MarathonAdminView.as_view())

]


