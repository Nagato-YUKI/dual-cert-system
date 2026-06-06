"""Archive service for material organization."""

import os
import shutil
from typing import Any

from app import db
from app.models.exam import Exam
from app.models.registration import Registration


def archive_by_exam(exam_id: int, base_archive_dir: str) -> dict:
    """Archive approved registration materials by class.

    Args:
        exam_id: The exam ID to archive.
        base_archive_dir: Base directory for archive storage.

    Returns:
        Dict with archive report info.
    """
    exam = db.session.execute(
        db.select(Exam).filter_by(id=exam_id)
    ).scalar_one_or_none()
    if not exam:
        return {"msg": "Exam not found"}

    registrations = db.session.execute(
        db.select(Registration).filter_by(exam_id=exam_id, status="approved")
    ).scalars().all()

    if not registrations:
        return {"msg": "No approved registrations to archive", "exam_id": exam_id}

    # Group by class
    grouped: dict[str, list[Any]] = {}
    for reg in registrations:
        class_name = reg.student.class_.name if reg.student and reg.student.class_ else "未分类"
        if class_name not in grouped:
            grouped[class_name] = []
        grouped[class_name].append(reg)

    archive_paths = []
    for class_name, regs in grouped.items():
        safe_class = _safe_filename(class_name)
        safe_exam = _safe_filename(exam.exam_name)
        archive_dir = os.path.join(base_archive_dir, safe_exam, safe_class)
        os.makedirs(archive_dir, exist_ok=True)

        for reg in regs:
            student_folder = os.path.join(
                archive_dir,
                f"{_safe_filename(reg.student.student_no)}_{_safe_filename(reg.student.name)}",
            )
            os.makedirs(student_folder, exist_ok=True)

            if reg.materials_path and os.path.exists(reg.materials_path):
                # Copy materials to archive folder
                if os.path.isfile(reg.materials_path):
                    shutil.copy2(reg.materials_path, student_folder)
                elif os.path.isdir(reg.materials_path):
                    dest = os.path.join(student_folder, os.path.basename(reg.materials_path))
                    shutil.copytree(reg.materials_path, dest, dirs_exist_ok=True)

        archive_paths.append(archive_dir)

    return {
        "exam_id": exam_id,
        "exam_name": exam.exam_name,
        "archived_classes": list(grouped.keys()),
        "total_students": len(registrations),
        "archive_paths": archive_paths,
    }


def list_archive_by_class(base_archive_dir: str) -> dict:
    """List archive directory structure grouped by class.

    Returns:
        Dict mapping class names to list of exam archive info.
    """
    result: dict[str, list[dict]] = {}
    if not os.path.exists(base_archive_dir):
        return result

    for exam_name in os.listdir(base_archive_dir):
        exam_path = os.path.join(base_archive_dir, exam_name)
        if not os.path.isdir(exam_path):
            continue

        for class_name in os.listdir(exam_path):
            class_path = os.path.join(exam_path, class_name)
            if not os.path.isdir(class_path):
                continue

            if class_name not in result:
                result[class_name] = []

            student_count = len(
                [d for d in os.listdir(class_path) if os.path.isdir(os.path.join(class_path, d))]
            )
            result[class_name].append({
                "exam_name": exam_name,
                "path": class_path,
                "student_count": student_count,
            })

    return result


def export_archive(exam_id: int, base_archive_dir: str, export_dir: str) -> str:
    """Export archived materials as a zip file.

    Returns:
        Path to the generated zip file.
    """
    exam = db.session.execute(
        db.select(Exam).filter_by(id=exam_id)
    ).scalar_one_or_none()
    if not exam:
        raise ValueError("Exam not found")

    safe_exam = _safe_filename(exam.exam_name)
    source = os.path.join(base_archive_dir, safe_exam)
    if not os.path.exists(source):
        raise ValueError("Archive not found for this exam")

    os.makedirs(export_dir, exist_ok=True)
    zip_path = os.path.join(export_dir, f"{safe_exam}_archive")
    shutil.make_archive(zip_path, "zip", source)
    return f"{zip_path}.zip"


def _safe_filename(name: str) -> str:
    """Return a filesystem-safe version of the given name."""
    return "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()
