from django.urls import path

from .views import ChallengeMarathonAPIView, MarathonDetailAPIView, MarathonDayAPIView, MarathonDayUserAPIView, StatisticUserMarathonAPIView

urlpatterns = [
    path("marathon/", ChallengeMarathonAPIView.as_view()),
    path("marathon/<int:pk>/", MarathonDetailAPIView.as_view()),
    path("marathon/<int:marathon_id>/daily/", MarathonDayAPIView.as_view()),
    path("marathon/<int:marathon_id>/day/", MarathonDayUserAPIView.as_view()),
    path("marathon/<int:marathon_id>/statistics/", StatisticUserMarathonAPIView.as_view()),
    path("marathon/<int:marathon_id>/statistics/user/<int:user_id>/", StatisticUserMarathonAPIView.as_view())

]


