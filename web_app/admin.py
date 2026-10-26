from django.contrib import admin

from .models import Category, Clint

# Register your models here.
# admin.site.register(Category)
# admin.site.register(Clint)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Clint)
class ClintAdmin(admin.ModelAdmin):
    pass
