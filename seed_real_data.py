"""Generate realistic mock data for Chinese university students."""

import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models.cert_type import CertType
from app.models.exam import Exam
from app.models.student import Student
from app.models.registration import Registration
from app.models.class_ import ClassModel
from app.models.certificate_record import CertificateRecord

app = create_app()
app.app_context().push()

# Clear existing data (keep students and classes)
print("Clearing old exam and cert data...")
from app.models.registration_rule import RegistrationRule
from app.models.review_log import ReviewLog
from app.models.operation_log import OperationLog

# Delete in order to respect FK constraints
ReviewLog.query.delete()
OperationLog.query.delete()
Registration.query.delete()
CertificateRecord.query.delete()
Exam.query.delete()
RegistrationRule.query.delete()
CertType.query.delete()
db.session.commit()

# Real Chinese university certificates
CERTIFICATES = [
    {
        "name": "大学英语四级考试(CET-4)",
        "category": "语言类",
        "description": "全国大学英语四级考试，衡量大学生英语基础能力的重要标准",
        "issuing_authority": "教育部考试中心",
        "is_required": True,
        "is_recommended": True,
    },
    {
        "name": "大学英语六级考试(CET-6)",
        "category": "语言类",
        "description": "全国大学英语六级考试，衡量大学生英语综合能力的高级标准",
        "issuing_authority": "教育部考试中心",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "全国计算机等级考试二级(Python)",
        "category": "计算机类",
        "description": "全国计算机等级考试二级Python语言程序设计",
        "issuing_authority": "教育部考试中心",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "全国计算机等级考试二级(MS Office)",
        "category": "计算机类",
        "description": "全国计算机等级考试二级MS Office高级应用",
        "issuing_authority": "教育部考试中心",
        "is_required": True,
        "is_recommended": True,
    },
    {
        "name": "普通话水平测试(PSC)",
        "category": "语言类",
        "description": "国家普通话水平测试，教师资格证必备条件",
        "issuing_authority": "国家语言文字工作委员会",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "教师资格证(中学)",
        "category": "职业资格",
        "description": "国家教师资格考试，从事教育教学工作的必备证书",
        "issuing_authority": "教育部教师资格认定指导中心",
        "is_required": False,
        "is_recommended": False,
    },
    {
        "name": "软考初级-程序员",
        "category": "计算机类",
        "description": "计算机技术与软件专业技术资格(水平)考试初级",
        "issuing_authority": "人力资源和社会保障部",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "软考中级-软件设计师",
        "category": "计算机类",
        "description": "计算机技术与软件专业技术资格(水平)考试中级",
        "issuing_authority": "人力资源和社会保障部",
        "is_required": False,
        "is_recommended": False,
    },
    {
        "name": "会计专业技术资格(初级)",
        "category": "职业资格",
        "description": "初级会计职称考试，财会领域入门证书",
        "issuing_authority": "财政部会计资格评价中心",
        "is_required": False,
        "is_recommended": False,
    },
    {
        "name": "华为HCIA-Datacom",
        "category": "厂商认证",
        "description": "华为认证ICT工程师-数通方向，网络技术基础认证",
        "issuing_authority": "华为技术有限公司",
        "is_required": False,
        "is_recommended": True,
    },
]

# Create certificates
cert_map = {}
for cert_data in CERTIFICATES:
    cert = CertType(**cert_data, status="active")
    db.session.add(cert)
    db.session.flush()
    cert_map[cert.name] = cert.id
    print(f"Created cert: {cert.name}")

db.session.commit()

# Real exam locations
LOCATIONS = [
    "教学楼A301", "教学楼A302", "教学楼B205", "教学楼B206",
    "语音室C101", "语音室C102", "语音室C103", "机房D201",
    "机房D202", "机房D203", "图书馆报告厅", "实验楼E301",
]

# Generate exams for each certificate (2025-2026 academic year)
now = datetime.now()
exams = []

for cert_name, cert_id in cert_map.items():
    # Each cert has 2-4 exams per year
    num_exams = random.randint(2, 4)
    for i in range(num_exams):
        # Spread exams across months
        month_offset = random.randint(-6, 6)
        exam_date = now + timedelta(days=month_offset * 30 + random.randint(-10, 10))

        reg_start = exam_date - timedelta(days=random.randint(45, 60))
        reg_end = exam_date - timedelta(days=random.randint(10, 20))

        status = "upcoming" if exam_date > now + timedelta(days=7) else (
            "ongoing" if exam_date > now - timedelta(days=1) else "completed"
        )

        exam = Exam(
            cert_type_id=cert_id,
            exam_name=f"{cert_name.split('(')[0]}第{i+1}批次考试",
            exam_date=exam_date.date(),
            registration_start=reg_start.date(),
            registration_end=reg_end.date(),
            exam_location=random.choice(LOCATIONS),
            max_capacity=random.randint(30, 120),
            fee=random.choice([0, 30, 50, 80]),
            status=status,
        )
        db.session.add(exam)
        db.session.flush()
        exams.append(exam)
        print(f"Created exam: {exam.exam_name} on {exam.exam_date}")

db.session.commit()

# Get all students
students = db.session.execute(db.select(Student)).scalars().all()
if not students:
    print("No students found! Please run seed data first.")
    exit(1)

# Generate registrations with realistic monthly distribution
print("\nGenerating registrations...")

# Status weights
STATUS_WEIGHTS = ["pending"] * 15 + ["approved"] * 30 + ["rejected"] * 10 + ["failed"] * 10 + ["passed"] * 35
REVIEW_STATUS_MAP = {
    "pending": "pending",
    "approved": "reviewed",
    "rejected": "reviewed",
    "failed": "reviewed",
    "passed": "reviewed",
}

reg_count = 0
for student in students:
    # Each student registers for 1-4 exams
    num_regs = random.randint(1, 4)
    chosen_exams = random.sample(exams, min(num_regs, len(exams)))

    for exam in chosen_exams:
        # Spread submit times across last 6 months
        days_ago = random.randint(0, 180)
        submit_time = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        status = random.choice(STATUS_WEIGHTS)
        review_status = REVIEW_STATUS_MAP[status]

        reg = Registration(
            student_id=student.id,
            exam_id=exam.id,
            status=status,
            submit_time=submit_time,
            review_status=review_status,
        )
        db.session.add(reg)
        reg_count += 1

db.session.commit()
print(f"Created {reg_count} registrations")

# Generate some certificate records for approved/passed students
print("\nGenerating certificate records...")
cert_records = 0
approved_regs = db.session.execute(
    db.select(Registration).filter(Registration.status.in_(["approved", "passed"]))
).scalars().all()

for reg in approved_regs:
    if random.random() < 0.7:  # 70% have actual certificate
        cert_no = f"CERT{reg.exam.cert_type_id:03d}{reg.student_id:04d}{random.randint(1000,9999)}"
        score = random.randint(60, 95)
        obtain_date = reg.exam.exam_date or now.date()

        record = CertificateRecord(
            student_id=reg.student_id,
            cert_type_id=reg.exam.cert_type_id,
            exam_id=reg.exam_id,
            certificate_no=cert_no,
            score=score,
            obtain_date=obtain_date,
            status="obtained",
        )
        db.session.add(record)
        cert_records += 1

db.session.commit()
print(f"Created {cert_records} certificate records")

print("\n=== Data generation complete ===")
print(f"Certificates: {len(CERTIFICATES)}")
print(f"Exams: {len(exams)}")
print(f"Registrations: {reg_count}")
print(f"Certificate Records: {cert_records}")
