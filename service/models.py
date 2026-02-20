from django.db import models



class UserSmall(models.Model):

    user_id = models.IntegerField()
    age = models.SmallIntegerField()
    male = models.BooleanField() #man True, woman False
    weight = models.SmallIntegerField()
    height = models.SmallIntegerField()


    def __str__(self):

        return str(self.user_id)

class Challenge(models.Model):

    challenge_id = models.IntegerField()

    approach = models.IntegerField()
    number_times = models.IntegerField()





class ChallengeMarathon(models.Model):

    user = models.ForeignKey(UserSmall, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    folder = models.CharField(max_length=100, default="challenge-marathon")

    image = models.CharField(max_length=100)

    points = models.BooleanField(default=False)
    callories = models.BooleanField(default=False)

    challenges = models.ManyToManyField(Challenge, related_name="marathon_challenge")

    start_date = models.DateField()
    end_date = models.DateField()

    man = models.BooleanField(default=False)
    woman = models.BooleanField(default=False)

    min_age = models.IntegerField()
    max_age = models.IntegerField()

    descriptions = models.TextField(max_length=300)


    def get_all_users(self):
        """
        Возвращает всех пользователей этого марафона и их записи.
        """
        # берем всех участников марафона через ChallengeMarathonUser
        user_ids = ChallengeMarathonUser.objects.filter(
            marathon=self
        ).values_list("user_id", flat=True)

        # получаем самих юзеров и сразу подгружаем их записи по дням
        return UserSmall.objects.filter(
            id__in=user_ids
        ).prefetch_related("marathon_day_usersmall")


class ChallengeMarathonUser(models.Model):
    
    user = models.ForeignKey(UserSmall, on_delete=models.CASCADE)

    marathon = models.ForeignKey(ChallengeMarathon, on_delete=models.CASCADE, related_name="marathon_user")



class MarathonDays(models.Model):

    marathon = models.ForeignKey(ChallengeMarathon, on_delete=models.CASCADE, related_name="marathon_days")

    date = models.DateField()



class MarathonDayUser(models.Model):

    user = models.ForeignKey(UserSmall, on_delete=models.CASCADE, related_name="marathon_day_usersmall")

    marathon_day = models.ForeignKey(MarathonDays, on_delete=models.CASCADE, related_name="marathon_day_user")

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="marathon_user_challenge")
    number_times = models.IntegerField(default=0)

    callories = models.DecimalField(decimal_places=2, max_digits=6)

    score = models.IntegerField(default=0)

    folder = models.CharField(default="marathon-day-user")

    video = models.CharField()


    status = models.CharField(choices=[("success", "success"), ("warning", "warning")], max_length=10)    


    class Meta:
        indexes = [
            models.Index(fields=["user", "marathon_day", "challenge"]),
        ]



