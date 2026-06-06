"""Generate realistic mock data for Chinese university students."""

import json
import random
from datetime import datetime, timedelta
from urllib.parse import quote

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.cert_type import CertType
from app.models.certificate_record import CertificateRecord
from app.models.class_ import ClassModel
from app.models.exam import Exam
from app.models.operation_log import OperationLog
from app.models.registration import Registration
from app.models.registration_rule import RegistrationRule
from app.models.review_log import ReviewLog
from app.models.student import Student
from app.models.training_material import TrainingMaterial
from app.models.user import User

app = create_app()
app.app_context().push()

# ============================================================
# 1. 清除旧数据（按外键依赖顺序删除）
# ============================================================
print("Clearing old data...")
ReviewLog.query.delete()
OperationLog.query.delete()
CertificateRecord.query.delete()
Registration.query.delete()
Exam.query.delete()
TrainingMaterial.query.delete()
RegistrationRule.query.delete()
CertType.query.delete()
User.query.delete()
db.session.commit()
print("Old data cleared.")

# ============================================================
# 2. 创建默认管理员用户
# ============================================================
admin = User(
    username="admin",
    password_hash=generate_password_hash("admin123"),
    role="admin",
    name="系统管理员",
)
db.session.add(admin)
db.session.commit()
print(f"Created admin user: {admin.username}")

# ============================================================
# 3. 更新学生姓名为真实中文姓名
# ============================================================
CHINESE_NAMES = [
    "张伟", "王芳", "李明", "刘洋", "陈静",
    "杨帆", "赵磊", "黄丽", "周强", "吴敏",
    "徐超", "孙婷", "马杰", "朱琳", "胡波",
    "郭颖", "林峰", "何雪", "高鑫", "罗丹",
    "梁浩", "宋佳", "郑宇", "谢瑶", "韩冰",
    "唐亮", "冯娟", "董鹏", "萧蕾", "程刚",
    "曹慧", "袁帅", "邓萍", "许凯", "傅玲",
    "沈毅", "曾婉", "彭飞", "吕梅", "苏威",
    "蒋蓉", "蔡旭", "贾楠", "丁昊", "魏茜",
    "薛骏", "叶薇", "阎博", "余晴", "潘辰",
]

students = db.session.execute(db.select(Student)).scalars().all()
if not students:
    print("No students found! Please create students first.")
    exit(1)

random.shuffle(CHINESE_NAMES)
for idx, student in enumerate(students):
    student.name = CHINESE_NAMES[idx % len(CHINESE_NAMES)]
    # Set id_card for login (password = last 6 digits of id_card)
    if not student.id_card:
        student.id_card = f"4401012000{student.student_no[-6:]}"
    # Generate Pollinations AI avatar URL
    prompt = quote(
        "professional avatar portrait of a Chinese student, "
        "simple background, digital art style"
    )
    student.avatar_url = (
        f"https://image.pollinations.ai/prompt/{prompt}"
        f"?width=128&height=128&seed={student.id}&nologo=true"
    )
db.session.commit()
print(f"Updated {len(students)} student names, id_cards, and avatar URLs.")

# ============================================================
# 4. 创建证书类型（人社类/专业类/校内引进）
# ============================================================
CERTIFICATES = [
    # --- 人社类 ---
    {
        "name": "CET-4",
        "category": "人社类",
        "description": "全国大学英语四级考试，衡量大学生英语基础能力的重要标准",
        "issuing_authority": "教育部考试中心",
        "is_required": True,
        "is_recommended": True,
    },
    {
        "name": "CET-6",
        "category": "人社类",
        "description": "全国大学英语六级考试，衡量大学生英语综合能力的高级标准",
        "issuing_authority": "教育部考试中心",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "普通话水平测试",
        "category": "人社类",
        "description": "国家普通话水平测试，教师资格证认定必备条件",
        "issuing_authority": "国家语言文字工作委员会",
        "is_required": False,
        "is_recommended": True,
    },
    # --- 专业类 ---
    {
        "name": "计算机二级Python",
        "category": "专业类",
        "description": "全国计算机等级考试二级Python语言程序设计",
        "issuing_authority": "教育部考试中心",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "计算机二级MS Office",
        "category": "专业类",
        "description": "全国计算机等级考试二级MS Office高级应用与设计",
        "issuing_authority": "教育部考试中心",
        "is_required": True,
        "is_recommended": True,
    },
    {
        "name": "教师资格证",
        "category": "专业类",
        "description": "国家教师资格考试，从事教育教学工作的必备证书",
        "issuing_authority": "教育部教师资格认定指导中心",
        "is_required": False,
        "is_recommended": False,
    },
    {
        "name": "会计初级",
        "category": "专业类",
        "description": "初级会计职称考试，财会领域入门资格证书",
        "issuing_authority": "财政部会计资格评价中心",
        "is_required": False,
        "is_recommended": False,
    },
    # --- 校内引进 ---
    {
        "name": "办公软件应用",
        "category": "校内引进",
        "description": "办公软件应用能力认证，涵盖Word、Excel、PPT等办公技能",
        "issuing_authority": "校内认证中心",
        "is_required": True,
        "is_recommended": True,
    },
    {
        "name": "网页设计",
        "category": "校内引进",
        "description": "网页设计与开发能力认证，涵盖HTML/CSS/JavaScript基础",
        "issuing_authority": "校内认证中心",
        "is_required": False,
        "is_recommended": True,
    },
    {
        "name": "数据库管理",
        "category": "校内引进",
        "description": "数据库管理与应用能力认证，涵盖SQL与数据库运维基础",
        "issuing_authority": "校内认证中心",
        "is_required": False,
        "is_recommended": False,
    },
    {
        "name": "创新创业",
        "category": "校内引进",
        "description": "创新创业实践能力认证，涵盖创业基础与项目实践",
        "issuing_authority": "校内认证中心",
        "is_required": False,
        "is_recommended": True,
    },
]

cert_map = {}
for cert_data in CERTIFICATES:
    cert = CertType(**cert_data, status="active")
    db.session.add(cert)
    db.session.flush()
    cert_map[cert.name] = cert.id
    print(f"  Created cert: {cert.name} ({cert.category})")

db.session.commit()

# ============================================================
# 5. 为每个证书类型生成 RegistrationRule
# ============================================================
RULE_TEMPLATES = {
    "CET-4": {
        "rule_content": "在校大学生均可报名参加CET-4考试，需修完大学英语相关课程。",
        "required_grades": "大一及以上",
        "required_majors": None,
        "prerequisites": "修完大学英语四级课程或同等学力",
    },
    "CET-6": {
        "rule_content": "已通过CET-4考试（425分及以上）的在校大学生方可报名。",
        "required_grades": "大二及以上",
        "required_majors": None,
        "prerequisites": "CET-4成绩425分及以上",
    },
    "普通话水平测试": {
        "rule_content": "在校大学生均可报名，师范类专业学生优先安排。",
        "required_grades": "大一及以上",
        "required_majors": "师范类专业优先",
        "prerequisites": "无特殊前置要求",
    },
    "计算机二级Python": {
        "rule_content": "在校大学生均可报名，建议具备Python编程基础。",
        "required_grades": "大一及以上",
        "required_majors": None,
        "prerequisites": "建议修完Python程序设计课程",
    },
    "计算机二级MS Office": {
        "rule_content": "在校大学生均可报名，建议具备Office办公软件使用基础。",
        "required_grades": "大一及以上",
        "required_majors": None,
        "prerequisites": "建议修完计算机应用基础课程",
    },
    "教师资格证": {
        "rule_content": "在校大三及以上学生可报名，需通过普通话水平测试（二级乙等及以上）。",
        "required_grades": "大三及以上",
        "required_majors": "师范类专业；非师范类需修完教育学、心理学课程",
        "prerequisites": "普通话水平测试二级乙等及以上",
    },
    "会计初级": {
        "rule_content": "在校大学生均可报名，需具备高中毕业及以上学历。",
        "required_grades": "大一及以上",
        "required_majors": "财会类专业优先",
        "prerequisites": "高中毕业及以上学历",
    },
    "办公软件应用": {
        "rule_content": "全校学生均可报名，无前置条件限制。",
        "required_grades": None,
        "required_majors": None,
        "prerequisites": "无",
    },
    "网页设计": {
        "rule_content": "全校学生均可报名，建议具备基本计算机操作能力。",
        "required_grades": None,
        "required_majors": None,
        "prerequisites": "建议了解HTML基础",
    },
    "数据库管理": {
        "rule_content": "全校学生均可报名，建议具备SQL基础知识。",
        "required_grades": None,
        "required_majors": "计算机相关专业优先",
        "prerequisites": "建议修完数据库原理课程",
    },
    "创新创业": {
        "rule_content": "全校学生均可报名，鼓励有创业意向或正在参与创业项目的学生参加。",
        "required_grades": None,
        "required_majors": None,
        "prerequisites": "无",
    },
}

for cert_name, cert_id in cert_map.items():
    template = RULE_TEMPLATES.get(cert_name, {
        "rule_content": "全校学生均可报名。",
        "required_grades": None,
        "required_majors": None,
        "prerequisites": "无",
    })
    rule = RegistrationRule(
        cert_type_id=cert_id,
        rule_content=template["rule_content"],
        required_grades=template["required_grades"],
        required_majors=template["required_majors"],
        prerequisites=template["prerequisites"],
    )
    db.session.add(rule)
    print(f"  Created rule for: {cert_name}")

db.session.commit()

# ============================================================
# 6. 生成 TrainingMaterial 数据
# ============================================================
MATERIAL_TEMPLATES = {
    "CET-4": [
        {"title": "CET-4核心词汇手册", "content": "涵盖四级考试高频词汇3000个，按主题分类整理，配有例句和记忆技巧。", "material_type": "document"},
        {"title": "CET-4听力训练专题", "content": "针对四级听力Section A/B/C的专项训练，含历年真题音频及解析。", "material_type": "video"},
        {"title": "CET-4在线模拟考试平台", "content": "提供全真模拟考试环境，自动评分与薄弱环节分析。", "material_type": "link"},
    ],
    "CET-6": [
        {"title": "CET-6高级词汇与阅读", "content": "六级核心词汇6000个，配合长篇阅读理解训练。", "material_type": "document"},
        {"title": "CET-6写作与翻译技巧", "content": "六级写作模板与翻译策略，含高分范文20篇。", "material_type": "document"},
    ],
    "普通话水平测试": [
        {"title": "普通话水平测试朗读作品60篇", "content": "官方指定朗读作品，含拼音标注与朗读示范音频。", "material_type": "document"},
        {"title": "普通话声韵调专项训练", "content": "针对声母、韵母、声调的发音纠正训练视频。", "material_type": "video"},
    ],
    "计算机二级Python": [
        {"title": "Python程序设计基础教程", "content": "覆盖二级考试全部知识点的系统教程，含大量编程实例。", "material_type": "document"},
        {"title": "Python二级真题精讲", "content": "近5年真题逐题讲解视频，重点分析高频考点。", "material_type": "video"},
    ],
    "计算机二级MS Office": [
        {"title": "MS Office高级应用教程", "content": "Word长文档排版、Excel数据分析、PPT设计三大模块全面讲解。", "material_type": "document"},
        {"title": "Office二级操作题专项训练", "content": "针对操作题的专项练习，含详细步骤演示视频。", "material_type": "video"},
    ],
    "教师资格证": [
        {"title": "综合素质考点精讲", "content": "教师资格证综合素质科目核心考点梳理与真题解析。", "material_type": "document"},
        {"title": "教育知识与能力重点笔记", "content": "教育学、心理学核心知识点归纳，含思维导图。", "material_type": "document"},
        {"title": "面试试讲示范视频", "content": "各学科面试试讲优秀示范，含评委点评。", "material_type": "video"},
    ],
    "会计初级": [
        {"title": "初级会计实务考点速记", "content": "初级会计实务科目核心考点精炼，配合典型例题。", "material_type": "document"},
        {"title": "经济法基础重点法条解读", "content": "经济法基础考试涉及的重要法律法规条文解读与案例分析。", "material_type": "document"},
    ],
    "办公软件应用": [
        {"title": "办公软件综合应用实训手册", "content": "Word文档处理、Excel数据处理、PPT演示制作综合实训项目。", "material_type": "document"},
        {"title": "Excel函数与数据透视表教程", "content": "常用函数及数据透视表的实操教学视频。", "material_type": "video"},
    ],
    "网页设计": [
        {"title": "HTML5+CSS3网页设计入门", "content": "从零开始学习网页设计与制作，含响应式布局实战。", "material_type": "document"},
        {"title": "JavaScript基础与交互效果", "content": "网页交互效果实现教程，含常见动效代码示例。", "material_type": "link"},
    ],
    "数据库管理": [
        {"title": "SQL语言基础与实战", "content": "SQL查询、增删改操作及多表关联查询实战教程。", "material_type": "document"},
        {"title": "MySQL数据库安装与配置指南", "content": "MySQL环境搭建、用户管理及基本运维操作视频。", "material_type": "video"},
    ],
    "创新创业": [
        {"title": "创新创业基础教程", "content": "创业意识培养、商业模式设计、创业计划书撰写指导。", "material_type": "document"},
        {"title": "大学生创业案例精选", "content": "10个典型大学生创业成功与失败案例分析。", "material_type": "link"},
    ],
}

material_count = 0
for cert_name, cert_id in cert_map.items():
    templates = MATERIAL_TEMPLATES.get(cert_name, [])
    for tmpl in templates:
        material = TrainingMaterial(
            cert_type_id=cert_id,
            title=tmpl["title"],
            content=tmpl["content"],
            file_path=None,
            material_type=tmpl["material_type"],
            is_public=True,
        )
        db.session.add(material)
        material_count += 1

db.session.commit()
print(f"Created {material_count} training materials.")

# ============================================================
# 7. 生成考试（使用更真实的考试名称）
# ============================================================
LOCATIONS = [
    "教学楼A301", "教学楼A302", "教学楼B205", "教学楼B206",
    "语音室C101", "语音室C102", "语音室C103", "机房D201",
    "机房D202", "机房D203", "图书馆报告厅", "实验楼E301",
]

now = datetime.now()

# 每个证书的考试名称模板
EXAM_NAME_TEMPLATES = {
    "CET-4": ["2025年上半年CET-4考试", "2025年下半年CET-4考试", "2026年上半年CET-4考试"],
    "CET-6": ["2025年上半年CET-6考试", "2025年下半年CET-6考试", "2026年上半年CET-6考试"],
    "普通话水平测试": ["2025年3月普通话水平测试", "2025年9月普通话水平测试", "2026年3月普通话水平测试"],
    "计算机二级Python": ["2025年3月计算机二级考试(Python)", "2025年9月计算机二级考试(Python)", "2026年3月计算机二级考试(Python)"],
    "计算机二级MS Office": ["2025年3月计算机二级考试(MS Office)", "2025年9月计算机二级考试(MS Office)", "2026年3月计算机二级考试(MS Office)"],
    "教师资格证": ["2025年上半年教师资格证考试(笔试)", "2025年下半年教师资格证考试(笔试)", "2026年上半年教师资格证考试(笔试)"],
    "会计初级": ["2025年初级会计职称考试", "2026年初级会计职称考试"],
    "办公软件应用": ["2025年春季办公软件应用认证", "2025年秋季办公软件应用认证", "2026年春季办公软件应用认证"],
    "网页设计": ["2025年春季网页设计认证", "2025年秋季网页设计认证", "2026年春季网页设计认证"],
    "数据库管理": ["2025年春季数据库管理认证", "2025年秋季数据库管理认证", "2026年春季数据库管理认证"],
    "创新创业": ["2025年春季创新创业认证", "2025年秋季创新创业认证", "2026年春季创新创业认证"],
}

# 每个证书的考试费用
EXAM_FEES = {
    "CET-4": 30,
    "CET-6": 30,
    "普通话水平测试": 50,
    "计算机二级Python": 80,
    "计算机二级MS Office": 80,
    "教师资格证": 70,
    "会计初级": 112,
    "办公软件应用": 0,
    "网页设计": 0,
    "数据库管理": 0,
    "创新创业": 0,
}

exams = []
for cert_name, cert_id in cert_map.items():
    name_list = EXAM_NAME_TEMPLATES.get(cert_name, [f"2025年{cert_name}考试"])
    fee = EXAM_FEES.get(cert_name, 0)

    for i, exam_name in enumerate(name_list):
        # 将考试日期分散到不同月份
        month_offset = (i - 1) * 6 + random.randint(-1, 1)
        exam_date = now + timedelta(days=month_offset * 30 + random.randint(-10, 10))

        reg_start = exam_date - timedelta(days=random.randint(45, 60))
        reg_end = exam_date - timedelta(days=random.randint(10, 20))

        if exam_date > now + timedelta(days=7):
            status = "upcoming"
        elif exam_date > now - timedelta(days=1):
            status = "ongoing"
        else:
            status = "completed"

        exam = Exam(
            cert_type_id=cert_id,
            exam_name=exam_name,
            exam_date=exam_date.date(),
            registration_start=reg_start.date(),
            registration_end=reg_end.date(),
            exam_location=random.choice(LOCATIONS),
            max_capacity=random.randint(30, 120),
            fee=fee,
            status=status,
        )
        db.session.add(exam)
        db.session.flush()
        exams.append(exam)
        print(f"  Created exam: {exam.exam_name} ({exam.exam_date})")

db.session.commit()

# ============================================================
# 8. 生成报名记录（含 ai_review_result 和 ai_review_score）
# ============================================================
print("\nGenerating registrations...")

STATUS_WEIGHTS = (
    ["pending"] * 15
    + ["approved"] * 30
    + ["rejected"] * 10
    + ["failed"] * 10
    + ["passed"] * 35
)
REVIEW_STATUS_MAP = {
    "pending": "pending",
    "approved": "reviewed",
    "rejected": "reviewed",
    "failed": "reviewed",
    "passed": "reviewed",
}

# AI 审核结果模板
AI_REVIEW_TEMPLATES = {
    "approved": [
        {"conclusion": "通过", "reason": "报名材料齐全，符合报名条件，建议通过审核。"},
        {"conclusion": "通过", "reason": "学生资质符合要求，前置条件已满足，审核通过。"},
        {"conclusion": "通过", "reason": "成绩达标，材料完整，建议批准报名。"},
    ],
    "rejected": [
        {"conclusion": "不通过", "reason": "前置证书未获得，不满足报名条件，建议驳回。"},
        {"conclusion": "不通过", "reason": "报名材料不完整，缺少必要证明文件，建议驳回。"},
        {"conclusion": "不通过", "reason": "年级不符合要求，当前年级未达到报名最低年级限制。"},
    ],
    "need_more_info": [
        {"conclusion": "需补充材料", "reason": "提交的成绩单模糊，请重新上传清晰扫描件。"},
        {"conclusion": "需补充材料", "reason": "缺少前置证书复印件，请补充后重新提交。"},
    ],
}

reg_count = 0
for student in students:
    num_regs = random.randint(1, 4)
    chosen_exams = random.sample(exams, min(num_regs, len(exams)))

    for exam in chosen_exams:
        days_ago = random.randint(0, 180)
        submit_time = now - timedelta(days=days_ago, hours=random.randint(0, 23))

        status = random.choice(STATUS_WEIGHTS)
        review_status = REVIEW_STATUS_MAP[status]

        # 为已审核的报名生成 AI 审核结果
        ai_review_result = None
        ai_review_score = None
        if status in ("approved", "rejected", "failed", "passed"):
            template_key = status if status in AI_REVIEW_TEMPLATES else "approved"
            if status in ("failed", "passed"):
                template_key = "approved"
            template = random.choice(AI_REVIEW_TEMPLATES[template_key])
            ai_review_result = json.dumps(template, ensure_ascii=False)
            ai_review_score = random.randint(60, 95)

        reg = Registration(
            student_id=student.id,
            exam_id=exam.id,
            status=status,
            submit_time=submit_time,
            review_status=review_status,
            ai_review_result=ai_review_result,
            ai_review_score=ai_review_score,
        )
        db.session.add(reg)
        reg_count += 1

db.session.commit()
print(f"Created {reg_count} registrations")

# ============================================================
# 9. 生成证书记录（增加状态多样性）
# ============================================================
print("\nGenerating certificate records...")

CERT_RECORD_STATUSES = ["obtained"] * 75 + ["expired"] * 15 + ["revoked"] * 10

cert_records = 0
approved_regs = db.session.execute(
    db.select(Registration).filter(Registration.status.in_(["approved", "passed"]))
).scalars().all()

for reg in approved_regs:
    if random.random() < 0.7:
        cert_no = f"CERT{reg.exam.cert_type_id:03d}{reg.student_id:04d}{random.randint(1000, 9999)}"
        score = random.randint(60, 95)
        obtain_date = reg.exam.exam_date or now.date()

        record_status = random.choice(CERT_RECORD_STATUSES)

        record = CertificateRecord(
            student_id=reg.student_id,
            cert_type_id=reg.exam.cert_type_id,
            exam_id=reg.exam_id,
            certificate_no=cert_no,
            score=score,
            obtain_date=obtain_date,
            status=record_status,
            source="system",
        )
        db.session.add(record)
        cert_records += 1

db.session.commit()
print(f"Created {cert_records} certificate records")

# ============================================================
# 完成
# ============================================================
print("\n=== Data generation complete ===")
print(f"Admin User: 1")
print(f"Students updated: {len(students)}")
print(f"Certificates: {len(CERTIFICATES)}")
print(f"Registration Rules: {len(cert_map)}")
print(f"Training Materials: {material_count}")
print(f"Exams: {len(exams)}")
print(f"Registrations: {reg_count}")
print(f"Certificate Records: {cert_records}")
