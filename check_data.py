"""Check database data."""

from app import create_app, db
from app.models.user import User
from app.models.student import Student
from app.models.cert_type import CertType
from app.models.exam import Exam
from app.models.registration import Registration

app = create_app()
app.app_context().push()

print("=== Database Data Check ===\n")

# Check admin
admin = db.session.execute(db.select(User).filter_by(username="admin")).scalar_one_or_none()
print(f"Admin user: {admin.username if admin else 'NOT FOUND'}")

# Check students
students = db.session.execute(db.select(Student)).scalars().all()
print(f"Students: {len(students)}")
if students:
    for s in students[:3]:
        print(f"  - {s.student_no}: {s.name}, id_card: {s.id_card}")

# Check cert types
certs = db.session.execute(db.select(CertType)).scalars().all()
print(f"\nCert Types: {len(certs)}")
if certs:
    for c in certs[:3]:
        print(f"  - {c.name} ({c.category})")

# Check exams
exams = db.session.execute(db.select(Exam)).scalars().all()
print(f"\nExams: {len(exams)}")
if exams:
    for e in exams[:3]:
        print(f"  - {e.exam_name}")

# Check registrations
regs = db.session.execute(db.select(Registration)).scalars().all()
print(f"\nRegistrations: {len(regs)}")
if regs:
    for r in regs[:3]:
        print(f"  - Student {r.student_id} -> Exam {r.exam_id}, status: {r.status}")

print("\n=== All Accounts ===")
print("Admin: admin / admin123")
for s in students:
    pwd = (s.id_card or "")[-6:] if s.id_card else ""
    print(f"Student: {s.student_no} / {pwd} (Name: {s.name})")
