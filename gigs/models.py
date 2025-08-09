from django.db import models
from accounts.models import TeacherProfile, Language

class Gig(models.Model):
    CATEGORY_CHOICES = (
        ('language_tutor', 'Language Tutor'),
        ('chirologist', 'Chirologist'),
    )

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='gigs')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    languages = models.ManyToManyField(Language)
    rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_duration = models.IntegerField(default=30)  # minimum duration in minutes
    about_service = models.TextField()
    experience = models.TextField()
    education = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.teacher.user_profile.user.email} - {self.title}"

class GigReview(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.UserProfile', on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('gig', 'user')

    def __str__(self):
        return f"{self.gig.title} - {self.rating} stars"
