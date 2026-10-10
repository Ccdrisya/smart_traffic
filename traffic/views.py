import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BulkUploadForm, CCTVImageUploadForm, get_location
from .models import CCTVImage, ModelWeights
from collections import defaultdict
from datetime import date

from django.utils import timezone

from .ml.inference import classify_congestion
from .models import Location
from django.db.models import Avg, Count

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "traffic/home.html")


LEVEL_HEX = {"LIGHT": "#198754", "MODERATE": "#FFC107", "HEAVY": "#DC3545"}


def dashboard(request):
    """Summary only: totals, recent days chart, and one row per location."""
    processed = CCTVImage.objects.exclude(processed_at__isnull=True)

    levels = {"LIGHT": 0, "MODERATE": 0, "HEAVY": 0}
    by_day = defaultdict(list)
    for captured_at, count in processed.values_list("captured_at", "total_vehicle_count"):
        count = count or 0
        by_day[timezone.localtime(captured_at).date()].append(count)
        levels[classify_congestion(count)] += 1

    day_rows = []
    for d in sorted(by_day)[-14:]:
        avg = round(sum(by_day[d]) / len(by_day[d]), 1)
        day_rows.append({
            "label": d.strftime("%d %b"),
            "avg": avg,
            "n": len(by_day[d]),
            "level": classify_congestion(avg),
        })
    latest = day_rows[-1] if day_rows else None

    chart_data = {
        "labels": [r["label"] for r in day_rows],
        "avg": [r["avg"] for r in day_rows],
        "colors": [LEVEL_HEX[r["level"]] for r in day_rows],
    }

    location_rows = []
    for row in (processed.values("location__name")
                .annotate(n=Count("id"), avg=Avg("total_vehicle_count"))
                .order_by("-n")):
        avg = round(row["avg"] or 0, 1)
        location_rows.append({
            "name": row["location__name"] or "Not set",
            "n": row["n"],
            "avg": avg,
            "level": classify_congestion(avg),
        })

    return render(request, "traffic/dashboard.html", {
        "total": sum(levels.values()),
        "levels": levels,
        "latest": latest,
        "chart_data": chart_data,
        "location_rows": location_rows,
    })


# def image_upload(request):
#     """Single upload: save the image with its capture time and location, then analyze it."""
#     if request.method == "POST":
#         form = CCTVImageUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             cctv_image = form.save(commit=False)
#             active_model = ModelWeights.objects.filter(is_active=True).first()
#             cctv_image.model_used = active_model
#             cctv_image.save()

#             if active_model:
#                 from .ml.inference import run_inference

#                 run_inference(cctv_image, active_model.weights_file.path)
#                 messages.success(request, "Image analyzed.")
#             else:
#                 messages.warning(
#                     request, "No active model uploaded yet - image saved but not analyzed."
#                 )
#             return redirect("traffic:image_result", pk=cctv_image.pk)
#     else:
#         form = CCTVImageUploadForm()
#     return render(request, "traffic/image_upload.html", {"form": form})


def bulk_upload(request):
    """Bulk upload: many images stamped on a schedule, each analyzed in turn."""
    active_model = ModelWeights.objects.filter(is_active=True).first()

    if request.method == "POST":
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if not active_model:
                form.add_error(
                    None,
                    "No active model yet. Upload one in the admin panel and tick 'Is active' first.",
                )
            else:
                from .ml.inference import run_inference

                location = get_location(form.cleaned_data["location_name"])
                done, failed = 0, 0
                for upload, captured_at in form.schedule():
                    cctv_image = CCTVImage.objects.create(
                        image=upload,
                        captured_at=captured_at,
                        location=location,
                        model_used=active_model,
                    )
                    try:
                        run_inference(cctv_image, active_model.weights_file.path)
                        done += 1
                    except Exception:
                        logger.exception("Analysis failed for image %s", cctv_image.pk)
                        failed += 1

                messages.success(request, f"Analyzed {done} image(s) for {location}.")
                if failed:
                    messages.warning(request, f"{failed} image(s) could not be analyzed.")
                return redirect("traffic:dashboard")
    else:
        form = BulkUploadForm()
    return render(request, "traffic/bulk_upload.html", {"form": form})


def image_result(request, pk):
    cctv_image = get_object_or_404(CCTVImage, pk=pk)
    return render(request, "traffic/image_result.html", {"cctv_image": cctv_image})

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LEVEL_CSS = {"LIGHT": "bg-success", "MODERATE": "bg-warning text-dark", "HEAVY": "bg-danger"}


def _section(key, title, groups, label_for):
    rows = []
    for k in sorted(groups):
        counts = groups[k]
        rows.append({
            "label": label_for(k),
            "images": len(counts),
            "total": sum(counts),
            "avg": round(sum(counts) / len(counts), 1),
        })
    return {
        "key": key,
        "title": title,
        "rows": rows,
        "chart_rows": rows[-31:],
        "busiest": max(rows, key=lambda r: r["avg"]) if rows else None,
        "quietest": min(rows, key=lambda r: r["avg"]) if rows else None,
    }


def analytics(request):
    """One page: day, weekday, hour and month patterns, expected congestion, charts."""
    qs = CCTVImage.objects.exclude(processed_at__isnull=True)
    location_id = request.GET.get("location", "")
    if location_id.isdigit():
        qs = qs.filter(location_id=int(location_id))

    by_day, by_weekday, by_hour, by_month, by_slot = (defaultdict(list) for _ in range(5))
    levels = {"LIGHT": 0, "MODERATE": 0, "HEAVY": 0}
    total_images = 0

    for captured_at, count in qs.values_list("captured_at", "total_vehicle_count"):
        t = timezone.localtime(captured_at)
        count = count or 0
        by_day[t.date()].append(count)
        by_weekday[t.weekday()].append(count)
        by_hour[t.hour].append(count)
        by_month[(t.year, t.month)].append(count)
        by_slot[(t.weekday(), t.hour)].append(count)
        levels[classify_congestion(count)] += 1
        total_images += 1

    sections = [
        _section("day", "Day wise", by_day, lambda k: k.strftime("%d %b %Y")),
        _section("weekday", "Weekday wise", by_weekday, lambda k: WEEKDAYS[k]),
        _section("hour", "Hour of day", by_hour, lambda k: f"{k:02d}:00"),
        _section("month", "Month wise", by_month, lambda k: date(k[0], k[1], 1).strftime("%b %Y")),
    ]
    chart_data = {
        s["key"]: {
            "labels": [r["label"] for r in s["chart_rows"]],
            "avg": [r["avg"] for r in s["chart_rows"]],
        }
        for s in sections
    }

    # Expected congestion grid: average count for each weekday + hour slot
    hours = sorted({h for _, h in by_slot})
    grid = []
    for wd in range(7):
        cells = []
        for h in hours:
            counts = by_slot.get((wd, h))
            if counts:
                avg = sum(counts) / len(counts)
                cells.append({
                    "avg": round(avg, 1),
                    "n": len(counts),
                    "css": LEVEL_CSS[classify_congestion(avg)],
                })
            else:
                cells.append(None)
        grid.append({"day": WEEKDAYS[wd][:3], "cells": cells})

    # "Check a time" form
    check, wd_i, hr_i = None, None, None
    try:
        wd_i, hr_i = int(request.GET["weekday"]), int(request.GET["hour"])
    except (KeyError, ValueError):
        wd_i = hr_i = None
    if wd_i is not None and 0 <= wd_i <= 6 and 0 <= hr_i <= 23:
        counts = by_slot.get((wd_i, hr_i))
        check = {"when": f"{WEEKDAYS[wd_i]} around {hr_i:02d}:00", "n": len(counts or [])}
        if counts:
            avg = sum(counts) / len(counts)
            level = classify_congestion(avg)
            check.update(avg=round(avg, 1), level=level.title(), css=LEVEL_CSS[level])

    return render(request, "traffic/analytics.html", {
        "total_images": total_images,
        "levels": levels,
        "sections": sections,
        "chart_data": chart_data,
        "hours": hours,
        "grid": grid,
        "check": check,
        "locations": Location.objects.order_by("name"),
        "location_id": location_id,
        "weekday_options": list(enumerate(WEEKDAYS)),
        "hour_options": range(24),
        "wd_i": wd_i,
        "hr_i": hr_i,
    })