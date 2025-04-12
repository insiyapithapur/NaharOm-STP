from django.db import models
from django.utils import timezone
from UserFeatures.models import UserRole, Post_for_sale, Buyers, Sales

class TransactionLog(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    TRANSACTION_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    no_of_units = models.IntegerField()
    per_unit_price = models.FloatField()
    total_price = models.FloatField()
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='initiated')
    post_for_sale = models.ForeignKey(Post_for_sale, on_delete=models.SET_NULL, null=True, blank=True)
    buyer = models.ForeignKey(Buyers, on_delete=models.SET_NULL, null=True, blank=True)
    sales = models.ForeignKey(Sales, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.user.mobile} - {self.transaction_type} - {self.status}"
