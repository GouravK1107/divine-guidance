from django.db import models

# Create your models here.
class Scripture(models.Model):
    TRADITION_CHOICES = [
        ("gita", "Bhagavad Gita"),
        ("quran", "Quran"),
        ("bible", "Bible"),
    ]

    tradition = models.CharField(
        max_length=20,
        choices=TRADITION_CHOICES
    )

    book = models.CharField(
        max_length=100,
        blank=True
    )

    chapter = models.IntegerField()

    verse = models.CharField(
        max_length=50
    )

    text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.tradition} - {self.chapter}:{self.verse}"