from django.contrib import admin
from .models import UserSmall, Challenge, ChallengeMarathon, ChallengeMarathonUser, MarathonDays, MarathonDayUser


admin.site.register(MarathonDayUser)

@admin.register(UserSmall)
class UserSmallAdmin(admin.ModelAdmin):
    list_display = ("pk", "user_id", "age", "male", "weight", "height")
    list_filter = ("male",)
    search_fields = ("user_id",)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("challenge_id", "approach", "number_times")
    search_fields = ("challenge_id",)


class ChallengeInline(admin.TabularInline):
    """Для отображения ManyToMany через промежуточный admin"""
    model = ChallengeMarathon.challenges.through
    extra = 1


@admin.register(ChallengeMarathon)
class ChallengeMarathonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user_id", "start_date", "end_date", "man", "woman", "min_age", "max_age")
    list_filter = ("man", "woman")
    search_fields = ("name", "folder")
    inlines = [ChallengeInline]
    exclude = ("challenges",)  # ManyToMany показываем через inline


@admin.register(ChallengeMarathonUser)
class ChallengeMarathonUserAdmin(admin.ModelAdmin):
    list_display = ("user", "marathon")
    list_filter = ("marathon",)
    search_fields = ("user__user_id", "marathon__name")


class MarathonDaysInline(admin.TabularInline):
    model = MarathonDays
    extra = 1


# Зарегистрируем MarathonDays через ChallengeMarathon для удобного редактирования
@admin.register(MarathonDays)
class MarathonDaysAdmin(admin.ModelAdmin):
    list_display = ("id", "marathon", "date")
    list_filter = ("marathon",)
    search_fields = ("marathon__name",)
