from django.contrib import admin
from .models import *

# ---------- Academic ----------
admin.site.register(LearningTrack)
admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Resource)
admin.site.register(Problem)
admin.site.register(UserTopicProgress)

# ---------- Core productivity ----------
admin.site.register(Task)
admin.site.register(Note)
admin.site.register(LearningGoal)
admin.site.register(StudySession)
admin.site.register(StudyStreak)

# ---------- Platform system ----------
@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_oauth", "is_active")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(PlatformAccount)
class PlatformAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "username", "last_synced")
    search_fields = ("user__username", "username")
    list_filter = ("platform",)

@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = ("account", "date", "problems_solved", "commits", "hours_spent", "xp")
    list_filter = ("account__platform", "date")

@admin.register(UserHeatmap)
class UserHeatmapAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "activity_score", "total_xp")

@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ("user", "total_xp", "level", "current_streak")

@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ("rank", "user", "xp", "calculated_at")