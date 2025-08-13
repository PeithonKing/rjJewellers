
from datetime import timedelta
from django.db import models
from django.utils.timezone import now

class Customer(models.Model):
    cid = models.CharField(primary_key=True, max_length=50, unique=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.cid}: {self.name} ({self.phone_number})"

class Invoice(models.Model):
    iid = models.CharField(primary_key=True, max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    referrer = models.ForeignKey(Customer, on_delete=models.SET_NULL, related_name='referred_invoices', null=True, blank=True, default=None)
    items = models.TextField(blank=True)

    loyalty_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loyalty_expiration_date = models.DateField()
    loyalty_points_status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('claimed', 'Claimed'),
        ('expired', 'Expired'),
    ], default='active')

    referral_points = models.DecimalField(max_digits=10, decimal_places=2, default=None, null=True, blank=True)
    referral_expiration_date = models.DateField(null=True, blank=True, default=None)
    referral_points_status = models.CharField(max_length=20, choices=[
        ('noreferral', 'No Referral'),
        ('active', 'Active'),
        ('claimed', 'Claimed'),
        ('expired', 'Expired'),
    ], null=True, blank=False, default="noreferral")

    def save(self, *args, **kwargs):
        loyalty_exp_days = 30
        referral_exp_days = 30
        loyalty_scaling_factor = 100
        referral_scaling_factor = 100

        self.loyalty_points = float(self.total_amount) / loyalty_scaling_factor
        self.referral_points = float(self.total_amount) / referral_scaling_factor if self.referrer else None

        self.loyalty_expiration_date = self.date + timedelta(days=loyalty_exp_days)
        self.referral_expiration_date = self.date + timedelta(days=referral_exp_days) if self.referrer else None

        self.refresh_loyalty_status()
        self.refresh_referral_status()

        super().save(*args, **kwargs)

    def refresh_loyalty_status(self):
        if self.loyalty_points_status == "claimed":
            return
        today = now().date()
        if self.loyalty_expiration_date < today:
            self.loyalty_points_status = 'expired'
        if self.loyalty_expiration_date >= today:
            self.loyalty_points_status = 'active'

    def refresh_referral_status(self):
        today = now().date()
        if not self.referrer:
            self.referral_points_status = 'noreferral'
        elif self.referral_points_status == "claimed":
            return
        elif self.referral_expiration_date < today:
            self.referral_points_status = 'expired'
        elif self.referral_expiration_date >= today:
            self.referral_points_status = 'active'

    def __str__(self):
        return f"Invoice for {self.customer.name} on {self.date}"
