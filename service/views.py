from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_list_or_404, get_object_or_404
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.db.models import Sum, Count, Q, OuterRef, Subquery, IntegerField, Prefetch
from django.db.models.functions import Coalesce
from django.db.models import (
    Sum,
    Count,
    Q,
    F,
    Value,
    IntegerField,
    DecimalField
)
from django.utils import timezone
import datetime
import json
from rest_framework.parsers import MultiPartParser, FormParser

from typing import List, Dict, Union
from django.db.models import Sum

from grpc_serivces.grpc_challenge.client import ChallengeInfo
from grpc_serivces.grpc_profile.client import ProfileInfo

from .models import ChallengeMarathon, Challenge, MarathonDays, ChallengeMarathonUser, UserSmall, MarathonDayUser, ClubMarathon, ClubUserr
from .serializers import MarathonDetailSerializer, MarathonSerializer, MarathonDayUserSerializer, StatisticUsersMarathonSerializer, ChallengeDailySerializer, ClubMarathonSerializer, ClubUserrSerializer

from utils.langs import LangsSignleton
from utils.s3_operations import S3Service


class ChallengeMarathonAPIView(APIView):

    serializer_class = MarathonSerializer
    langs = LangsSignleton

    permission_classes = [AllowAny]

    s3_service = S3Service


    def get(self, request):

        user_id = request.user.id

        challenge_type_str = request.GET.get("type", "false").lower()

        challenge_type = challenge_type_str == "true"

        if challenge_type:
            queryset = ChallengeMarathon.objects.filter(user__user_id=user_id)

        else:
            queryset = ChallengeMarathon.objects.filter(marathon_user__user__user_id=user_id)


        return Response(self.serializer_class(queryset, many=True).data, status=status.HTTP_200_OK)
    
    def str_to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true")
        return False  

    def post(self, request):
        lang = request.query_params.get("lang", "ru")
        langs = self.langs(lang)

        user_id = request.user.id

        name = request.data.get("name")
        challenges = request.data.get("challenges")

        start_date: List[Dict[Union[str, int]]]  = request.data.get("start_date")

        end_date = request.data.get("end_date")

        man = self.str_to_bool(request.data.get("man"))
        
        woman = self.str_to_bool(request.data.get("woman"))
        points = self.str_to_bool(request.data.get("points", False))
        callories = self.str_to_bool(request.data.get("callories", False))

        min_age = request.data.get("min_age")
        max_age = request.data.get("max_age")

        descriptions = request.data.get("descriptions")

        if not "image" in request.FILES:

            return Response({"message": langs.lang_msg("not_image")}, status=status.HTTP_400_BAD_REQUEST)
        
        image = request.FILES.get("image")

        if (len(challenges) == 0):
            return Response({"message": langs.lang_msg("challenge_empty").format(challenge_empty=str(challenges))}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            return Response({"message": "Invalid date format"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(challenges, str):

            challenges: List[Dict[Union[str, int]]] = json.loads(challenges)

        with transaction.atomic():
            user_data_dict = ProfileInfo().get_profile(user_id)

            user_small_data, craeted = UserSmall.objects.get_or_create(
                user_id=user_id,
                age=user_data_dict.age,
                male=user_data_dict.gender,
                weight=user_data_dict.weight,
                height=user_data_dict.height
            )

            challenge_objects = []
            for ch in challenges:
                obj = Challenge.objects.create(
                    challenge_id=ch.get("id"),
                    approach=ch.get("approach", 5),
                    number_times=ch.get("number_times", 10)
                )
                challenge_objects.append(obj)

            marathon = ChallengeMarathon.objects.create(
                user=user_small_data,  
                name=name,
                image=image.name,
                start_date=start_date,
                end_date=end_date,
                min_age=min_age,
                max_age=max_age,
                woman=woman,
                man=man,
                descriptions=descriptions,
                points=points,
                callories=callories
            )

            marathon.save()

            marathon.challenges.set(challenge_objects)  

            start = marathon.start_date
            end = marathon.end_date

            days = (end - start).days + 1

            
            existing = set(
                MarathonDays.objects
                .filter(marathon=marathon)
                .values_list("date", flat=True)
            )

            objs = [
                MarathonDays(marathon=marathon, date=start + datetime.timedelta(days=i))
                for i in range(days)
                if (start + datetime.timedelta(days=i)) not in existing
            ]

            MarathonDays.objects.bulk_create(objs)

            marathon_user, created = ChallengeMarathonUser.objects.get_or_create(
                user=user_small_data, 
                marathon=marathon
            )

            transaction.on_commit(
                lambda: self.s3_service().upload_file(marathon.folder, marathon.image, image)
            )

        return Response({"message": str(marathon.pk)}, status=status.HTTP_200_OK)

        


class MarathonDetailAPIView(APIView):

    serializer_class = MarathonDetailSerializer
    langs = LangsSignleton

    permission_classes = [AllowAny]

    def get(self, request, **kwargs):

        marathon = get_object_or_404(ChallengeMarathon, pk=kwargs["pk"])

        return Response(self.serializer_class(marathon, context={"challenges": marathon.challenges}).data, status=status.HTTP_200_OK)


    def post(self, request, **kwargs):
        
        lang = request.query_params.get("lang", "ru")
        user_id = request.user.id

        langs = self.langs(lang)

        marathon = get_object_or_404(ChallengeMarathon, pk=kwargs["pk"])

        user_data_dict = ProfileInfo().get_profile(user_id)
        today = datetime.date.today()

        if (user_data_dict.gender == ""):
            return Response({"message": langs.lang_msg("male_is_none")}, status=status.HTTP_400_BAD_REQUEST)

        if (user_data_dict.age <= marathon.min_age and user_data_dict.age >= marathon.max_age):
            return Response({"message": langs.lang_msg("age_not_valid").format(min_age=marathon.min_age, max_age=marathon.max_age)}, status=status.HTTP_403_FORBIDDEN)
        
        user_is_man = bool(user_data_dict.gender)

        allowed = marathon.man if user_is_man else marathon.woman

        if not allowed:

            male = langs.lang_msg("man" if not user_is_man else "woman")
            return Response(
                {"message": langs.lang_msg("male_not_valid").format(male=male)},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if (today >= marathon.start_date):
            return Response({"message": langs.lang_msg("marathon_exp")}, status=status.HTTP_403_FORBIDDEN)

        user_small_qs = UserSmall.objects.filter(user_id=user_id)

        if user_small_qs.exists():
            # Берём первый
            user_small_data = user_small_qs.first()
            # Обновляем актуальные данные
            user_small_data.age = user_data_dict.age
            user_small_data.male = user_data_dict.gender
            user_small_data.weight = user_data_dict.weight
            user_small_data.height = user_data_dict.height
            user_small_data.save()

            # Удаляем дубли, если есть
            user_small_qs.exclude(id=user_small_data.id).delete()
        else:
            # Создаём новый
            user_small_data = UserSmall.objects.create(
                user_id=user_id,
                age=user_data_dict.age,
                male=user_data_dict.gender,
                weight=user_data_dict.weight,
                height=user_data_dict.height
            )

        # Создаём привязку к марафону
        marathon_user, created = ChallengeMarathonUser.objects.get_or_create(
            user=user_small_data,
            marathon=marathon
        )
        return Response({"message": "success"}, status=status.HTTP_200_OK)



class MarathonDayAPIView(APIView):

    serializer_class = ...

    permission_classes = [AllowAny]

   
    def get(self, request, marathon_id):
        user_id = request.user.id
        today = timezone.now().date()

        # 1️⃣ все дни марафона
        marathon_days = MarathonDays.objects.filter(
            marathon_id=marathon_id
        ).order_by("date")

        # 2️⃣ все референсные челленджи марафона
        marathon_challenges = list(
            ChallengeMarathon.objects.get(pk=marathon_id)
            .challenges.all()
            .values("id", "approach", "number_times")
        )
        print(marathon_challenges)

        # 3️⃣ все записи пользователя для этого марафона
        user_records = MarathonDayUser.objects.filter(
            user__user_id=user_id,
            marathon_day__marathon_id=marathon_id
        ).values(
            "marathon_day_id", "challenge_id"
        ).annotate(
            total_number_times=Sum("number_times")
        )

        print(user_records)

        # 4️⃣ превратим в dict для быстрого поиска
        records_map = {}
        for rec in user_records:
            records_map.setdefault(rec["marathon_day_id"], {})[rec["challenge_id"]] = rec["total_number_times"]

        days = []

        for index, day in enumerate(marathon_days, start=1):
            if day.date > today:
                status_ = "waiting"
            else:
                day_records = records_map.get(day.id, {})
                print(day_records)        
                if not day_records:
                    status_ = "danger"
                else:
                    all_ok = True
                    for ch in marathon_challenges:
                        done_times = day_records.get(ch["id"], 0)
                        if done_times < ch["number_times"] * ch["approach"]:
                            all_ok = False
                            break
                    status_ = "success" if all_ok else "warning"

            days.append({
                "day": index,
                "status": status_
            })


        challenge_grpc = ChallengeInfo()

        challenges = []

        challenges_marathon = Challenge.objects.filter(marathon_challenge__pk=marathon_id)

        for c in challenges_marathon:
            try:

                challenge = challenge_grpc.get_challenge(c.challenge_id)
            except:
                continue

            challenges.append({"challenge_id": c.challenge_id, "cv_name": challenge.cv_name, "description": challenge.description, "name": challenge.name})

        response = {
            "challenges": challenges,
            "days": days
        }

        return Response(response)
    


    def delete(self, request, marathon_id):

        user_id = request.user.id

        marathon = get_object_or_404(ChallengeMarathon, pk=marathon_id, user__user_id=user_id)
        pk = marathon.pk
        marathon.delete()

        return Response({"message": pk}, status=status.HTTP_200_OK)

    


class MarathonDayUserAPIView(APIView):

    permission_classes = [AllowAny]


    serializer_class = MarathonDayUserSerializer


    parser_classes = (MultiPartParser, FormParser)  

    s3_serivce = S3Service

    def get(self, request, marathon_id):

        user_id = request.user.id
        lang = request.query_params.get("lang", "ru")


        challenge_id = request.query_params.get("challenge_id")
        langs = LangsSignleton(lang)

        if challenge_id is None:
            print(challenge_id)
            return Response({"message": langs.lang_msg("challenge_id_none")}, status=status.HTTP_400_BAD_REQUEST)
        
        marathon = get_object_or_404(ChallengeMarathon, pk=marathon_id)

        challenge = get_object_or_404(
                Challenge,
                challenge_id=challenge_id,
                marathon_challenge=marathon
            )
        
        print("challenges", challenge)
        
        today = datetime.date.today()

        if not (marathon.start_date <= today <= marathon.end_date):
            return Response(
                {"message": langs.lang_msg("out_date")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        marathon_day = get_object_or_404(MarathonDays, marathon=marathon, date=today)

        marathon_day_user = MarathonDayUser.objects.filter(user__user_id=user_id, marathon_day=marathon_day, challenge=challenge).order_by("id")

        marathon_user = marathon_day_user.last()

        print(marathon_day_user)
        print(marathon_user.number_times if marathon_user else 0)

        return Response(self.serializer_class(marathon_day, 
                                              context={"approach": marathon_day_user.count(), 
                                                       "challenge_id": challenge_id, 
                                                       "number_times": marathon_user.number_times if marathon_user else 0}).data, 
                                              status=status.HTTP_200_OK)


    def post(self, request, marathon_id):

        user_id = request.user.id

        lang = request.query_params.get("lang", "ru")

        langs = LangsSignleton(lang)

        callories = request.data.get("callories", 0)
        number_times = request.data.get("number_times", 0)
        score = request.data.get("score", 0)
        challenge_id = request.data.get("challenge_id", None)

        video = request.FILES.get("video", None)

        if video is None:

            return Response({"message": langs.lang_msg("non_video")}, status=status.HTTP_400_BAD_REQUEST)
        
        if challenge_id is None:
            return Response({"message": langs.lang_msg("challenge_id_none")}, status=status.HTTP_400_BAD_REQUEST)
        
        video_name = video.name
        marathon = get_object_or_404(ChallengeMarathon, pk=marathon_id)

        challenge = get_object_or_404(
                Challenge,
                challenge_id=challenge_id,
                marathon_challenge=marathon
            )

        today = datetime.date.today()

        marathon_day = MarathonDays.objects.filter(date=today, marathon=marathon)

        if not marathon_day.exists():
            return Response({"message": langs.lang_msg("date_out")}, status=status.HTTP_403_FORBIDDEN)

        if not (marathon.start_date <= today <= marathon.end_date):
            return Response(
                {"message": langs.lang_msg("out_date")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        marathon_day = marathon_day.first()
        
        status_ = "success" if number_times == challenge.number_times else "warning"
        
        user = get_object_or_404(UserSmall, user_id=user_id)

        with transaction.atomic():

            challenge_user = MarathonDayUser.objects.create(
                user=user,
                marathon_day=marathon_day,
                challenge=challenge,
                number_times=number_times,
                score=score,
                callories=callories,
                video=video_name,
                status=status_
            )

            transaction.on_commit(
                lambda: self.s3_serivce().upload_video(challenge_user.folder, challenge_user.video, video)  
            )

        return Response({"message": "success"}, status=status.HTTP_200_OK)
  
  


class StatisticUserMarathonAPIView(APIView):
    serializer_class = StatisticUsersMarathonSerializer
    permission_classes = [AllowAny]

    def get(self, request, marathon_id):
        lang = request.query_params.get("lang", "ru")
        order_by_field = request.query_params.get("order_by", None)
        direction = request.query_params.get("direction", "desc")

        marathon = get_object_or_404(ChallengeMarathon, pk=marathon_id)

        result = []
        for user in marathon.get_all_users():
            success_day = 0
            warning_day = 0
            failed_day = 0
            calories = 0.0
            scores = 0

            for ch in marathon.challenges.all():
                days = MarathonDays.objects.filter(marathon=marathon).order_by("date")
                for day in days:
                    user_marathon = MarathonDayUser.objects.filter(
                        user=user, challenge=ch, marathon_day=day
                    )

                    if not user_marathon.exists():
                        failed_day += 1
                        continue

                    if user_marathon.filter(status="success").count() == ch.approach:
                        success_day += 1
                    else:
                        warning_day += 1

                    calories += float(user_marathon.aggregate(callories=Sum("callories"))["callories"] or 0)
                    scores += int(user_marathon.aggregate(score=Sum("score"))["score"] or 0)

            result.append({
                "user": user,
                "user_id": user.user_id,
                "success_days": success_day,
                "failed_days": failed_day,
                "warning_days": warning_day,
                "callories": calories,
                "scores": scores
            })

        # сортировка
        if order_by_field in {"failed_days", "success_days", "warning_days", "callories", "scores"}:
            reverse = direction == "desc"
            result.sort(key=lambda x: x[order_by_field], reverse=reverse)

        serializer = self.serializer_class(result, many=True, context={"lang": lang})
        return Response({"users": serializer.data})



class MarathonAdminView(APIView):

    permission_classes = [AllowAny]


    def get(self, request, marathon_id, user_id):

        user_id_owner = request.user.id

        lang = request.query_params.get("lang", "ru")
        select_day = int(request.query_params.get("day", 1))

        if not user_id:
            return Response(
                {"message": "user id is not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.now().date()

        # ✅ проверка что пользователь админ марафона
        marathon = ChallengeMarathon.objects.filter(
            pk=marathon_id,
            user__user_id=user_id_owner
        ).first()

        if not marathon:
            return Response(
                {"message": "you is not admin in marathon"},
                status=status.HTTP_403_FORBIDDEN
            )

        # --------------------------------------------------
        # DAYS (НЕ ТРОГАЕМ ЛОГИКУ)
        # --------------------------------------------------

        marathon_days = list(
            MarathonDays.objects.filter(
                marathon_id=marathon_id
            ).order_by("date")
        )

        marathon_challenges = list(
            marathon.challenges.all().values(
                "id", "approach", "number_times"
            )
        )

        user_records = MarathonDayUser.objects.filter(
            user__user_id=user_id,
            marathon_day__marathon_id=marathon_id
        ).values(
            "marathon_day_id", "challenge_id"
        ).annotate(
            total_number_times=Sum("number_times")
        )

        records_map = {}
        for rec in user_records:
            records_map.setdefault(
                rec["marathon_day_id"], {}
            )[rec["challenge_id"]] = rec["total_number_times"]

        days = []

        for index, day in enumerate(marathon_days, start=1):

            if day.date > today:
                status_ = "waiting"
            else:
                day_records = records_map.get(day.id, {})

                if not day_records:
                    status_ = "danger"
                else:
                    all_ok = True

                    for ch in marathon_challenges:
                        done_times = day_records.get(ch["id"], 0)

                        if done_times < ch["number_times"] * ch["approach"]:
                            all_ok = False
                            break

                    status_ = "success" if all_ok else "warning"

            days.append({
                "day": index,
                "status": status_
            })

        # --------------------------------------------------
        # ✅ ВЫБОР ДНЯ ПО НОМЕРУ (НЕ ID)
        # --------------------------------------------------

        try:
            selected_day_obj = marathon_days[select_day - 1]
        except IndexError:
            return Response(
                {"message": "day not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------------------------
        # ✅ ВИДЕО ПОЛЬЗОВАТЕЛЯ ЗА ЭТОТ ДЕНЬ
        # --------------------------------------------------

        videos_queryset = MarathonDayUser.objects.filter(
            user__user_id=user_id,
            marathon_day_id=selected_day_obj.id
        )

        s3_service = S3Service()

        challenges = ChallengeDailySerializer(
            videos_queryset,
            many=True,
            context={"s3_service": s3_service}
        ).data

        # --------------------------------------------------

        response = {
            "challenges": challenges,
            "days": days
        }

        return Response(response, status=status.HTTP_200_OK)



