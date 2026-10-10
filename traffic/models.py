from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ModelWeights(models.Model):
    """
    A trained YOLOv8 checkpoint (.pt file), fine-tuned externally on
    Google Colab using the BMD-45 dataset, then uploaded here by the admin.
    """

    name = models.CharField(max_length=150, help_text="e.g. 'YOLOv8n - BMD45 v1'")
    weights_file = models.FileField(upload_to="model_weights/")
    is_active = models.BooleanField(
        default=False,
        help_text="Only one model should be active at a time — used for all new inferences.",
    )
    notes = models.TextField(blank=True, help_text="Training notes: epochs, dataset size, mAP, etc.")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploaded_weights")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    def save(self, *args, **kwargs):
        # Ensure only one active model at a time
        if self.is_active:
            ModelWeights.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Location(models.Model):
    """A camera / junction that images belong to, e.g. 'MG Road Junction'."""

    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CCTVImage(models.Model):
    """A single uploaded CCTV image submitted for inference."""

    image = models.ImageField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # When the snapshot was actually taken (entered at upload). Drives all time-based analytics.
    captured_at = models.DateTimeField(default=timezone.now)
    location = models.ForeignKey(
        Location, related_name="images", on_delete=models.SET_NULL, null=True, blank=True,
    )

    model_used = models.ForeignKey(
        ModelWeights, related_name="analyzed_images", on_delete=models.SET_NULL, null=True, blank=True,
    )

    annotated_image = models.ImageField(upload_to="detections/", blank=True, null=True)
    total_vehicle_count = models.PositiveIntegerField(default=0)
    congestion_level = models.CharField(
        max_length=10,
        choices=[("LIGHT", "Light"), ("MODERATE", "Moderate"), ("HEAVY", "Heavy")],
        blank=True,
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Image #{self.pk} - {self.congestion_level or 'unprocessed'}"


class VehicleClassCount(models.Model):
    """Per-class detection count for a given CCTV image (car: 4, bus: 1, ...)."""

    cctv_image = models.ForeignKey(CCTVImage, related_name="class_counts", on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    count = models.PositiveIntegerField(default=0)
    avg_confidence = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("cctv_image", "class_name")

    def __str__(self):
        return f"{self.class_name}: {self.count}"