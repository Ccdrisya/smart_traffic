from django.contrib import admin
from .models import ModelWeights, CCTVImage, VehicleClassCount


@admin.register(ModelWeights)
class ModelWeightsAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "uploaded_by", "uploaded_at")
    list_filter = ("is_active",)


class VehicleClassCountInline(admin.TabularInline):
    model = VehicleClassCount
    extra = 0


@admin.register(CCTVImage)
class CCTVImageAdmin(admin.ModelAdmin):
    list_display = ("id", "uploaded_at", "total_vehicle_count", "congestion_level", "model_used")
    list_filter = ("congestion_level", "model_used")
    inlines = [VehicleClassCountInline]