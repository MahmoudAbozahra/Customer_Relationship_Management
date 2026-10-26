from django.db import models

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=250)
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Clint(models.Model):
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    tall = models.IntegerField(blank=True, null=True)
    wight = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    class Meta:
        ordering = ["-created_at"]
