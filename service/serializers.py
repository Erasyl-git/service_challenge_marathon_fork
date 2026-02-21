from rest_framework import serializers

from .models import Challenge, ChallengeMarathon, ChallengeMarathonUser, MarathonDays, MarathonDayUser

import datetime

from utils.s3_operations import S3Service
from grpc_serivces.grpc_challenge.client import ChallengeInfo
from utils.langs import LangsSignleton

from utils.s3_operations import S3Service
from grpc_serivces.grpc_profile.client import ProfileInfo

class ChallengeSerializer(serializers.ModelSerializer):

    class Meta:

        model = Challenge
        fields = ["approach", "number_times"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        challenge = ChallengeInfo().get_challenge(instance.challenge_id)

        data["cv_name"] = challenge.cv_name

        data["name"] = challenge.name

        return data




class MarathonSerializer(serializers.ModelSerializer):

    class Meta:

        model = ChallengeMarathon
        fields = ["id", "start_date", "name"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        today = datetime.date.today()

        data["active"] =  today >= instance.start_date and today <= instance.end_date

        return data


class MarathonDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChallengeMarathon
        fields = ["name", "start_date", "end_date", "min_age", "max_age", "descriptions"]


    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["image"] = S3Service().get_presigned_url(f"{instance.folder}/{instance.image}")
        challenges = self.context.get("challenges")

        lang = self.context.get("lang", "ru")

        langs = LangsSignleton(lang)

        if challenges is not None:

            data["challenges"] = ChallengeSerializer(challenges, many=True).data

        data["gender"] = ", ".join(filter(None, [instance.man*langs.lang_msg("men"), instance.woman*langs.lang_msg("women")]))

        return data
        

class MarathonDayUserSerializer(serializers.ModelSerializer):

    class Meta:

        model = MarathonDayUser
        fields = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        challenges = instance.marathon_day.marathon.challenges.filter(challenge_id=instance.challenge.challenge_id).first()
        data["current_approach"] = challenges.approach
        data["user_approach"] = self.context.get("approach", 0)
        data["current_times"] = challenges.number_times
        data["user_times"] = instance.number_times

        return data


class StatisticUsersMarathonSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(read_only=True)
    age = serializers.IntegerField(source="user.age", read_only=True)
    success_days = serializers.IntegerField(read_only=True)
    failed_days = serializers.IntegerField(read_only=True)
    warning_days = serializers.IntegerField(read_only=True)
    callories = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    scores = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    gender = serializers.CharField(read_only=True)
    image = serializers.CharField(read_only=True)   

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = instance["user"]
        lang = self.context.get("lang", "ru")
        langs = LangsSignleton(lang)

        profile_user = ProfileInfo()
        profile_data = profile_user.get_profile(user.user_id)

        data["image"] = profile_data.image
        data["name"] = profile_data.first_name
        data["gender"] = langs.lang_msg("man" if user.male else "woman")

        return data



class ChallengeDailySerializer(serializers.ModelSerializer):

    video = serializers.SerializerMethodField()

    class Meta:

        model = MarathonDayUser
        fields = ["video"]

    def get_video(self, obj: MarathonDayUser) -> str:

        s3_service: S3Service = self.context.get("s3_service", False)

        if not s3_service:

            return ""
        
        response = s3_service.get_presigned_url(f"{obj.folder}/{obj.video}")

        return response


# class StatisticUserDetailSerializer(serializers.ModelSerializer):

#     ...
