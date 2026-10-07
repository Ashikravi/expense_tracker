from decimal import Decimal

from django.db import models


class Expense(models.Model):
    class Category(models.TextChoices):
        FOOD = "food", "Food"
        TRANSPORT = "transport", "Transport"
        BILLS = "bills", "Bills"
        ENTERTAINMENT = "entertainment", "Entertainment"
        SHOPPING = "shopping", "Shopping"
        HEALTH = "health", "Health"
        OTHER = "other", "Other"

    title = models.CharField(max_length=100)
    # Money is stored as integer paise so sums are exact (no float drift in SQLite).
    amount_paise = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    spent_on = models.DateField(db_index=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-spent_on", "-id"]  # most recent first; id breaks same-day ties

    @property
    def amount(self) -> Decimal:
        return Decimal(self.amount_paise) / 100

    def __str__(self):
        return f"{self.title} ({self.amount})"
