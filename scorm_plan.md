# SCORM 1.2 Export Implementation Plan

## Goal
Enable users to export a generated course as a SCORM 1.2 compliant ZIP package. This allows the course to be uploaded to any standard LMS (Learning Management System).

## Features
1.  **Standard SCORM 1.2 Manifest**: Generate `imsmanifest.xml` dynamically based on the course structure.
2.  **Static HTML Generation**: Convert the Markdown content (Concept, Exercise, Quiz) into static HTML files.
3.  **SCORM API Integration**: Include a JavaScript adapter to communicate with the LMS.
    *   Track **Completion Status** (incomplete -> completed).
    *   (Optional) Track **Score** based on the quiz results.
4.  **ZIP Packaging**: Bundle all assets (HTML, CSS, JS, XML) into a single downloadable ZIP file.

## Technical Approach

### Backend (`app/services/scorm_exporter.py`)
*   New service class `ScormExporter`.
*   Method `create_package(course_id)`:
    1.  Fetch course and chapter data from DB.
    2.  Create a temporary directory.
    3.  Generate `imsmanifest.xml`.
    4.  For each chapter:
        *   Convert Markdown -> HTML (using a template).
        *   Inject SCORM API scripts.
    5.  Copy static assets (CSS, JS).
    6.  Zip the directory.
    7.  Return the ZIP file.

### API Endpoint (`app/main.py`)
*   `GET /courses/{course_id}/export/scorm`
    *   Returns: `FileResponse` (application/zip)

### Frontend
*   Add "Export SCORM" button to `ResultPage` (Course Detail) and `DashboardPage`.

## SCORM Details
*   **Manifest**: Will define one `<organization>` (the course) and multiple `<item>`s (chapters).
*   **Tracking**:
    *   On page load: `LMSInitialize("")`
    *   On completion (e.g., reaching bottom or passing quiz): `LMSSetValue("cmi.core.lesson_status", "completed")`
    *   On exit: `LMSFinish("")`

## Questions for User
1.  Do you want to track **Quiz Scores** in the LMS, or just **Completion** (viewed)?
2.  Should we export the entire course as one SCORM package, or allow individual chapter export? (Usually entire course is better).
