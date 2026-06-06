"""Import service for batch data import."""

from typing import Any

import pandas as pd

from app import db
from app.models.certificate_record import CertificateRecord
from app.models.cert_type import CertType
from app.models.class_ import ClassModel
from app.models.exam import Exam
from app.models.student import Student


def import_students(file_path: str) -> dict:
    """Import students from Excel/CSV file.

    Expected columns: student_no, name, class_name, phone, email, id_card
    """
    df = _read_file(file_path)
    results = {"success": [], "errors": []}

    for idx, row in df.iterrows():
        try:
            _validate_student_row(row)

            # Find or create class
            class_name = str(row.get("class_name", "")).strip()
            class_obj = None
            if class_name:
                class_obj = db.session.execute(
                    db.select(ClassModel).filter_by(name=class_name)
                ).scalar_one_or_none()
                if not class_obj:
                    class_obj = ClassModel(name=class_name)
                    db.session.add(class_obj)
                    db.session.flush()

            student_no = str(row.get("student_no", "")).strip()
            existing = db.session.execute(
                db.select(Student).filter_by(student_no=student_no)
            ).scalar_one_or_none()
            if existing:
                raise ValueError(f"Student number {student_no} already exists")

            student = Student(
                student_no=student_no,
                name=str(row.get("name", "")).strip(),
                class_id=class_obj.id if class_obj else None,
                phone=str(row.get("phone", "")).strip() if pd.notna(row.get("phone")) else None,
                email=str(row.get("email", "")).strip() if pd.notna(row.get("email")) else None,
                id_card=str(row.get("id_card", "")).strip() if pd.notna(row.get("id_card")) else None,
            )
            db.session.add(student)
            db.session.flush()
            results["success"].append({"row": idx + 1, "student_no": student_no})
        except Exception as e:
            results["errors"].append({"row": idx + 1, "error": str(e)})

    db.session.commit()
    return results


def import_exam_results(file_path: str) -> dict:
    """Import exam results from Excel/CSV file.

    Expected columns: student_no, cert_type_name, exam_name, score, exam_date
    """
    df = _read_file(file_path)
    results = {"success": [], "errors": []}

    for idx, row in df.iterrows():
        try:
            student_no = str(row.get("student_no", "")).strip()
            cert_type_name = str(row.get("cert_type_name", "")).strip()
            exam_name = str(row.get("exam_name", "")).strip()

            student = db.session.execute(
                db.select(Student).filter_by(student_no=student_no)
            ).scalar_one_or_none()
            if not student:
                raise ValueError(f"Student {student_no} not found")

            cert_type = db.session.execute(
                db.select(CertType).filter_by(name=cert_type_name)
            ).scalar_one_or_none()
            if not cert_type:
                raise ValueError(f"Certificate type {cert_type_name} not found")

            exam = db.session.execute(
                db.select(Exam).filter_by(exam_name=exam_name, cert_type_id=cert_type.id)
            ).scalar_one_or_none()

            score = float(row["score"]) if pd.notna(row.get("score")) else None
            exam_date = str(row["exam_date"]).strip() if pd.notna(row.get("exam_date")) else None

            record = CertificateRecord(
                student_id=student.id,
                cert_type_id=cert_type.id,
                exam_id=exam.id if exam else None,
                score=score,
                obtain_date=exam_date,
                status="obtained",
                source="manual_import",
            )
            db.session.add(record)
            db.session.flush()
            results["success"].append({"row": idx + 1, "student_no": student_no})
        except Exception as e:
            results["errors"].append({"row": idx + 1, "error": str(e)})

    db.session.commit()
    return results


def import_cert_records(file_path: str) -> dict:
    """Import certificate records from Excel/CSV file.

    Expected columns: student_no, cert_type_name, certificate_no, obtain_date, score
    """
    df = _read_file(file_path)
    results = {"success": [], "errors": []}

    for idx, row in df.iterrows():
        try:
            student_no = str(row.get("student_no", "")).strip()
            cert_type_name = str(row.get("cert_type_name", "")).strip()
            certificate_no = str(row.get("certificate_no", "")).strip()

            student = db.session.execute(
                db.select(Student).filter_by(student_no=student_no)
            ).scalar_one_or_none()
            if not student:
                raise ValueError(f"Student {student_no} not found")

            cert_type = db.session.execute(
                db.select(CertType).filter_by(name=cert_type_name)
            ).scalar_one_or_none()
            if not cert_type:
                raise ValueError(f"Certificate type {cert_type_name} not found")

            # Check duplicate certificate_no
            if certificate_no:
                existing = db.session.execute(
                    db.select(CertificateRecord).filter_by(certificate_no=certificate_no)
                ).scalar_one_or_none()
                if existing:
                    raise ValueError(f"Certificate number {certificate_no} already exists")

            score = float(row["score"]) if pd.notna(row.get("score")) else None
            obtain_date = str(row["obtain_date"]).strip() if pd.notna(row.get("obtain_date")) else None

            record = CertificateRecord(
                student_id=student.id,
                cert_type_id=cert_type.id,
                certificate_no=certificate_no,
                score=score,
                obtain_date=obtain_date,
                status="obtained",
                source="manual_import",
            )
            db.session.add(record)
            db.session.flush()
            results["success"].append({"row": idx + 1, "student_no": student_no})
        except Exception as e:
            results["errors"].append({"row": idx + 1, "error": str(e)})

    db.session.commit()
    return results


def generate_template(import_type: str) -> str:
    """Generate an Excel template file for the given import type.

    Returns the file path of the generated template.
    """
    import os

    templates_dir = os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "templates")
    os.makedirs(templates_dir, exist_ok=True)

    if import_type == "students":
        df = pd.DataFrame(
            columns=["student_no", "name", "class_name", "phone", "email", "id_card"]
        )
        df.loc[0] = ["20230001", "张三", "2024级软件技术1班", "13800138000", "zhangsan@example.com", "350102200001011234"]
        path = os.path.join(templates_dir, "students_template.xlsx")
    elif import_type == "exam_results":
        df = pd.DataFrame(
            columns=["student_no", "cert_type_name", "exam_name", "score", "exam_date"]
        )
        df.loc[0] = ["20230001", "计算机等级考试", "2024年上半年计算机等级考试", "85", "2024-06-15"]
        path = os.path.join(templates_dir, "exam_results_template.xlsx")
    elif import_type == "cert_records":
        df = pd.DataFrame(
            columns=["student_no", "cert_type_name", "certificate_no", "obtain_date", "score"]
        )
        df.loc[0] = ["20230001", "计算机等级考试", "CERT20240001", "2024-06-20", "85"]
        path = os.path.join(templates_dir, "cert_records_template.xlsx")
    else:
        raise ValueError(f"Unknown import type: {import_type}")

    df.to_excel(path, index=False)
    return path


def _read_file(file_path: str) -> pd.DataFrame:
    """Read Excel or CSV file into DataFrame."""
    if file_path.lower().endswith(".csv"):
        return pd.read_csv(file_path)
    return pd.read_excel(file_path)


def _validate_student_row(row: Any) -> None:
    """Validate required fields for a student row."""
    if not str(row.get("student_no", "")).strip():
        raise ValueError("student_no is required")
    if not str(row.get("name", "")).strip():
        raise ValueError("name is required")
