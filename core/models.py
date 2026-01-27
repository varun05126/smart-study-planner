from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# ==================================================
#                ACADEMIC STRUCTURE
# ==================================================

class LearningTrack(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    track = models.ForeignKey(LearningTrack, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.track.name} - {self.name}"


class Topic(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


# ==================================================
#                RESOURCES & PRACTICE
# ==================================================

class Resource(models.Model):
    RESOURCE_TYPES = [
        ("video", "YouTube / Video"),
        ("article", "Article / Blog"),
        ("course", "Course"),
        ("book", "Book / PDF"),
        ("docs", "Documentation"),
        ("notes", "Notes"),
        ("practice", "Practice Platform"),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=255)
    url = models.URLField()
    type = models.CharField(max_length=15, choices=RESOURCE_TYPES)
    is_best = models.BooleanField(default=False)
    short_description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Problem(models.Model):
    DIFFICULTY = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="problems")
    title = models.CharField(max_length=200)
    platform = models.CharField(max_length=50)
    url = models.URLField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY)

    def __str__(self):
        return f"{self.title} ({self.platform})"


class UserTopicProgress(models.Model):
    STATUS = [
        ("not_started", "Not Started"),
        ("learning", "Learning"),
        ("completed", "Completed"),
        ("revising", "Revising"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topic_progress")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS, default="not_started")
    mastery = models.PositiveIntegerField(default=0)
    last_studied = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "topic")

    def __str__(self):
        return f"{self.user} - {self.topic} ({self.status})"


# ==================================================
#                PRODUCTIVITY CORE
# ==================================================

class Task(models.Model):

    TASK_TYPES = [
        ("assignment", "Assignment"),
        ("study", "Study"),
        ("revision", "Revision"),
        ("project", "Project"),
        ("exam", "Exam Prep"),
        ("reading", "Reading"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)

    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    custom_subject = models.CharField(max_length=150, blank=True)

    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default="study")
    material = models.FileField(upload_to="tasks/", blank=True, null=True)

    deadline = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    completed = models.BooleanField(default=False)

    needs_help = models.BooleanField(default=False)
    ai_solution = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ==================================================
#              TASK AI CHAT SYSTEM
# ==================================================

class TaskMessage(models.Model):
    SENDER = [("user", "User"), ("ai", "AI")]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.task.title} - {self.sender}"


# ==================================================
#                     NOTES
# ==================================================

class Note(models.Model):
    VISIBILITY = [("private", "Private"), ("public", "Public")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)

    subject = models.CharField(max_length=150, blank=True)  # ✅ NEW

    title = models.CharField(max_length=200)
    text_content = models.TextField(blank=True)
    file = models.FileField(upload_to="notes/", blank=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY, default="private")
    created_at = models.DateTimeField(auto_now_add=True)
    


# ==================================================
#                AI LEARNING GOALS
# ==================================================

class LearningGoal(models.Model):
    STATUS = [("planned", "Planned"), ("learning", "Learning"), ("completed", "Completed")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals")
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=15, choices=STATUS, default="planned")

    ai_solution = models.TextField(blank=True)
    is_satisfied = models.BooleanField(null=True, blank=True)
    satisfaction_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ==================================================
#                STUDY ENGINE
# ==================================================

class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_sessions")
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField()
    study_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.user} - {self.duration_minutes} min"


class StudyStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="study_streak")
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.current_streak} days"


# ==================================================
#           MULTI-PLATFORM ACTIVITY ENGINE
# ==================================================

class Platform(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    base_url = models.URLField(blank=True)
    uses_public_api = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PlatformAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="platform_accounts")
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, related_name="accounts")

    username = models.CharField(max_length=150)
    profile_url = models.URLField(blank=True)

    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "platform")

    def __str__(self):
        return f"{self.user} → {self.platform.name} ({self.username})"


class DailyActivity(models.Model):
    account = models.ForeignKey(PlatformAccount, on_delete=models.CASCADE, related_name="activities")
    date = models.DateField()

    problems_solved = models.PositiveIntegerField(default=0)
    commits = models.PositiveIntegerField(default=0)
    hours_spent = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    xp = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("account", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.account.user} - {self.account.platform.name} - {self.date}"


class UserHeatmap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="heatmap")
    date = models.DateField()

    total_xp = models.PositiveIntegerField(default=0)
    activity_score = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} - {self.date}"


class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="stats")

    # -------------------
    # PLATFORM USERNAMES (optional, helper cache)
    # -------------------
    github_username = models.CharField(max_length=150, blank=True, null=True)
    leetcode_username = models.CharField(max_length=150, blank=True, null=True)
    gfg_username = models.CharField(max_length=150, blank=True, null=True)
    codeforces_username = models.CharField(max_length=150, blank=True, null=True)
    hackerrank_username = models.CharField(max_length=150, blank=True, null=True)

    # -------------------
    # GITHUB
    # -------------------
    total_commits = models.PositiveIntegerField(default=0)
    github_xp = models.PositiveIntegerField(default=0)

    # -------------------
    # LEETCODE
    # -------------------
    leetcode_solved = models.PositiveIntegerField(default=0)
    leetcode_xp = models.PositiveIntegerField(default=0)

    # -------------------
    # GFG
    # -------------------
    gfg_solved = models.PositiveIntegerField(default=0)
    gfg_xp = models.PositiveIntegerField(default=0)

    # -------------------
    # CODEFORCES
    # -------------------
    codeforces_solved = models.PositiveIntegerField(default=0)
    codeforces_xp = models.PositiveIntegerField(default=0)

    # -------------------
    # HACKERRANK
    # -------------------
    hackerrank_solved = models.PositiveIntegerField(default=0)
    hackerrank_xp = models.PositiveIntegerField(default=0)

    # -------------------
    # GLOBAL TOTALS
    # -------------------
    total_xp = models.PositiveIntegerField(default=0)
    total_problems = models.PositiveIntegerField(default=0)
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # -------------------
    # STREAK + LEVEL
    # -------------------
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.total_xp} XP"


class LeaderboardEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leaderboard_entries")
    xp = models.PositiveIntegerField()
    rank = models.PositiveIntegerField()
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return f"{self.rank}. {self.user}"
    