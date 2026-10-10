import re
from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import CCTVImage, Location


def get_location(name):
    """Return the Location with this name (ignoring case and extra spaces), creating it if needed."""
    name = " ".join((name or "").split())
    if not name:
        return None
    location = Location.objects.filter(name__iexact=name).first()
    if location is None:
        location = Location.objects.create(name=name)
    return location


def natural_key(name):
    """Sort key so img2.png comes before img10.png."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", name)]


def build_schedule(files, start_at, interval_minutes, images_per_day=None):
    """
    Pair each file (sorted by filename) with a capture time.

    No images_per_day: start, start+interval, start+2*interval, ...
    With images_per_day: after that many images, jump to the same start time on the next day.
    """
    files = sorted(files, key=lambda f: natural_key(f.name))
    step = timedelta(minutes=interval_minutes)
    schedule = []
    for i, f in enumerate(files):
        if images_per_day:
            day, slot = divmod(i, images_per_day)
            when = start_at + timedelta(days=day) + step * slot
        else:
            when = start_at + step * i
        schedule.append((f, when))
    return schedule


class DateTimeLocalInput(forms.DateTimeInput):
    """Browser date + time picker (<input type="datetime-local">)."""

    input_type = "datetime-local"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


class MultipleImageField(forms.ImageField):
    """An ImageField that accepts several files at once and returns a list."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            data = [d for d in data if d.name.lower().endswith(IMAGE_EXTENSIONS)]
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)]

class CCTVImageUploadForm(forms.ModelForm):
    """Single upload: one image, when it was captured, and where."""

    location_name = forms.CharField(
        max_length=120,
        required=False,
        label="Location / camera name",
        help_text="For example the camera name shown on the image. Images with the same name are grouped together.",
    )

    class Meta:
        model = CCTVImage
        fields = ["image", "captured_at"]
        labels = {"captured_at": "Captured at"}
        widgets = {"captured_at": DateTimeLocalInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["captured_at"].initial = timezone.now
        self.fields["captured_at"].show_hidden_initial = False

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.location = get_location(self.cleaned_data.get("location_name"))
        if commit:
            obj.save()
        return obj


class BulkUploadForm(forms.Form):
    """Bulk upload: many images stamped on a schedule (day wise, time wise, month wise)."""

    MAX_FILES = 60

    images = MultipleImageField(label="CCTV images")
    location_name = forms.CharField(max_length=120, label="Location / camera name")
    start_at = forms.DateTimeField(
        label="First image captured at",
        widget=DateTimeLocalInput(),
        initial=lambda: timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0),
    )
    interval_minutes = forms.IntegerField(
        min_value=1, max_value=10080, initial=60, label="Minutes between images",
    )
    images_per_day = forms.IntegerField(
        min_value=1,
        required=False,
        label="Images per day (optional)",
        help_text="Leave blank for one continuous run. If set, every this many images the schedule moves to the next day, starting again at the first time.",
    )

    def clean_images(self):
        files = self.cleaned_data["images"]
        if not files:
            raise forms.ValidationError("Choose at least one image.")
        if len(files) > self.MAX_FILES:
            raise forms.ValidationError(
                f"Please upload at most {self.MAX_FILES} images at a time."
            )
        return files

    def clean(self):
        cleaned = super().clean()
        per_day = cleaned.get("images_per_day")
        interval = cleaned.get("interval_minutes")
        if per_day and interval and (per_day - 1) * interval >= 1440:
            self.add_error(
                "images_per_day",
                "That many images at this interval would run past 24 hours. Lower one of them.",
            )
        return cleaned

    def schedule(self):
        """List of (file, captured_at) pairs. Call only after is_valid()."""
        d = self.cleaned_data
        return build_schedule(
            d["images"], d["start_at"], d["interval_minutes"], d.get("images_per_day")
        )