# Deep Learning-Based Smart Traffic Monitoring System Using CCTV Images

A Django-based traffic monitoring system that uses YOLOv8 to detect and classify vehicles in CCTV images, estimate congestion levels, and analyze historical traffic patterns.

## Overview

Traditional traffic monitoring often requires manual observation of CCTV footage. This project automates vehicle detection and counting from static CCTV snapshots using deep learning.

The system processes uploaded images, identifies vehicles belonging to 14 Indian vehicle classes, calculates per-class vehicle counts, and estimates traffic congestion based on the total number of detected vehicles. It also stores results for historical analysis and provides time-based analytics to identify busy and quiet traffic periods.

## Features

- **Vehicle Detection:** Detect vehicles in uploaded CCTV images using YOLOv8.
- **Vehicle Classification:** Identify vehicles across 14 Indian vehicle classes.
- **Vehicle Counting:** Display total and per-class vehicle counts.
- **Congestion Estimation:** Categorize congestion as Light, Moderate, or Heavy based on predefined thresholds.
- **Single and Bulk Upload:** Process individual images or multiple images.
- **Capture Details:** Record image capture time and location.
- **Visual Results:** Display detected vehicles with bounding boxes and confidence scores.
- **Historical Records:** Store image analysis results in a MySQL database.
- **Time-Based Analytics:** Analyze traffic patterns by day, weekday, hour, and month.
- **Peak Period Analysis:** Identify the busiest and quietest periods using historical records.
- **Location Filtering:** Filter historical analysis by location.
- **Model Management:** Allow the administrator to manage model-weight files.

## Modules

### 1. Model Management

Allows the administrator to upload, view, activate, and delete model-weight files used for vehicle detection.

### 2. Vehicle Detection and Congestion Analysis

- Upload single CCTV images or bulk image collections.
- Provide capture time and location information.
- Detect and classify vehicles using YOLOv8.
- Display bounding boxes and confidence scores.
- Generate per-class vehicle counts.
- Estimate congestion levels.
- Store analysis results in MySQL.

### 3. Time-Based Analytics

- Retrieve previously stored analysis records.
- Group results by day, weekday, hour, and month.
- Display historical traffic patterns through charts.
- Identify the busiest and quietest periods.
- Filter analytics by location.
- Show expected congestion for a selected weekday and hour based on historical average vehicle counts.

## Congestion Classification

The system uses predefined thresholds based on the total number of detected vehicles in an image.

| Total Vehicle Count | Congestion Level |
|---|---|
| Below 8 | Light |
| 8–19 | Moderate |
| 20 or more | Heavy |

This is a count-based estimation method and does not account for vehicle size, road capacity, or vehicle movement.

## Technology Stack

- **Programming Language:** Python
- **Web Framework:** Django
- **Deep Learning / Object Detection:** YOLOv8
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Dataset:** BMD-45 vehicle dataset

## System Workflow

1. The user uploads a CCTV image or a batch of images.
2. The system validates the uploaded images and obtains the active detection model.
3. YOLOv8 detects and classifies vehicles.
4. The system calculates vehicle counts by class.
5. A congestion level is assigned based on the total vehicle count.
6. The results and associated capture details are stored in MySQL.
7. Users can view results, historical records, and time-based analytics.

## Database

The system uses MySQL to maintain the data required for image analysis, model management, and traffic analytics.

The main data stores represented in the system design are:

- `Model_weights` — model-weight information.
- `Location` — location information.
- `CCTV_image` — image records and associated capture details.
- `Vehicle_count` — vehicle-count information.

These names represent the data stores in the project design; actual database table names may differ depending on the implementation.

## Installation and Setup

### Prerequisites

- Python
- MySQL Server
- Git
- A compatible YOLOv8 model-weight file
- Required Python dependencies

### Steps

**1. Clone the repository**

```bash
git clone <your-repository-url>
cd <your-project-folder>
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

On Linux or macOS:

```bash
source venv/bin/activate
```

**3. Install dependencies**

If the project contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**4. Configure MySQL**

Create the required database and configure the database connection in the Django project settings. Use your own local database credentials.

**5. Apply database migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

**6. Start the development server**

```bash
python manage.py runserver
```

Open the local URL shown in the terminal to access the application.

> Note: The installation steps assume a standard Django project structure. Adjust the commands and configuration to match the repository. The exact dependency list, database name, model-weight path, and environment variables should be taken from the actual source code.

## Project Scope and Limitations

- Processes static CCTV images rather than continuous live video.
- Requires uploaded images and associated capture details.
- Estimates congestion using fixed vehicle-count thresholds.
- Uses historical averages for expected-congestion analysis.
- Does not currently implement real-time video processing, multi-object tracking, speed estimation, accident detection, number-plate recognition, or traffic-signal control.
- Historical analytics depend on the availability and quality of stored records.

## Future Enhancements

- Integrate real-time CCTV video processing.
- Incorporate road capacity and vehicle-type weighting into congestion estimation.
- Add multi-object tracking and vehicle speed estimation.
- Explore improved traffic forecasting techniques.
- Extend monitoring and visualization capabilities.

## Project Information

**Project Title:** Deep Learning-Based Smart Traffic Monitoring System Using CCTV Images

**Framework:** Django

**Detection Model:** YOLOv8

**Database:** MySQL

**Project Type:** Academic Mini Project

---

*This project demonstrates the application of deep learning and web technologies to automated vehicle detection, traffic congestion estimation, and historical traffic analysis.*
