from django.core.management.base import BaseCommand

from traffic.ml.inference import classify_congestion
from traffic.ml.vehicle_weights import weighted_load
from traffic.models import CCTVImage


class Command(BaseCommand):
    help = "Recalculate the weighted load and congestion level of every analyzed image from its saved class counts."

    def handle(self, *args, **options):
        updated = 0
        images = CCTVImage.objects.exclude(processed_at__isnull=True).prefetch_related("class_counts")
        for img in images:
            counts = {c.class_name: c.count for c in img.class_counts.all()}
            load = weighted_load(counts)
            img.weighted_load = load
            img.congestion_level = classify_congestion(load)
            img.save(update_fields=["weighted_load", "congestion_level"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Recalculated {updated} image(s)."))