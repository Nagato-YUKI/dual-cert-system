"""Take screenshots of all pages for the project."""
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"
SHOT_DIR = "screenshots"


def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # 1. Login page
        page.goto(f"{BASE}/login", wait_until="networkidle")
        page.screenshot(path=f"{SHOT_DIR}/01_login.png", full_page=False)
        print("01_login.png")

        # 2. Login error - wrong admin password
        page.fill("#admin-login-form input[name='username']", "admin")
        page.fill("#admin-login-form input[name='password']", "wrongpass")
        page.click("#admin-login-form button[type='submit']")
        time.sleep(1.5)
        page.screenshot(path=f"{SHOT_DIR}/02_login_error.png", full_page=False)
        print("02_login_error.png")

        # 3. Student login error
        page.click("#student-tab")
        time.sleep(0.5)
        page.fill("#student-login-form input[name='student_no']", "20240001")
        page.fill("#student-login-form input[name='password']", "wrongpass")
        page.click("#student-login-form button[type='submit']")
        time.sleep(1.5)
        page.screenshot(path=f"{SHOT_DIR}/03_student_login_error.png", full_page=False)
        print("03_student_login_error.png")

        # 4. Admin login
        page.click("#admin-tab")
        time.sleep(0.5)
        page.fill("#admin-login-form input[name='username']", "admin")
        page.fill("#admin-login-form input[name='password']", "admin123")
        page.click("#admin-login-form button[type='submit']")
        page.wait_for_url("**/admin**", timeout=5000)
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/04_admin_dashboard.png", full_page=False)
        print("04_admin_dashboard.png")

        # 5. Admin certificates
        page.goto(f"{BASE}/admin/certificates", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/05_admin_certificates.png", full_page=False)
        print("05_admin_certificates.png")

        # 6. Admin exams
        page.goto(f"{BASE}/admin/exams", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/06_admin_exams.png", full_page=False)
        print("06_admin_exams.png")

        # 7. Admin reviews
        page.goto(f"{BASE}/admin/reviews", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/07_admin_reviews.png", full_page=False)
        print("07_admin_reviews.png")

        # 8. Admin bigscreen
        page.goto(f"{BASE}/admin/bigscreen", wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=f"{SHOT_DIR}/08_admin_bigscreen.png", full_page=False)
        print("08_admin_bigscreen.png")

        # 9. Student login
        page.goto(f"{BASE}/login", wait_until="networkidle")
        page.click("#student-tab")
        time.sleep(0.5)
        page.fill("#student-login-form input[name='student_no']", "20240001")
        page.fill("#student-login-form input[name='password']", "010001")
        page.click("#student-login-form button[type='submit']")
        page.wait_for_url("**/student**", timeout=5000)
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/09_student_dashboard.png", full_page=False)
        print("09_student_dashboard.png")

        # 10. Student certificates - all
        page.goto(f"{BASE}/student/certificates", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/10_student_certificates_all.png", full_page=False)
        print("10_student_certificates_all.png")

        # 11. Student certificates - 人社类
        page.click("#tab-renshe")
        time.sleep(1.5)
        page.screenshot(path=f"{SHOT_DIR}/11_student_certificates_renshe.png", full_page=False)
        print("11_student_certificates_renshe.png")

        # 12. Student certificates - 专业类
        page.click("#tab-zhuanye")
        time.sleep(1.5)
        page.screenshot(path=f"{SHOT_DIR}/12_student_certificates_professional.png", full_page=False)
        print("12_student_certificates_professional.png")

        # 13. Student certificates - 校内引进
        page.click("#tab-xiaonei")
        time.sleep(1.5)
        page.screenshot(path=f"{SHOT_DIR}/13_student_certificates_school.png", full_page=False)
        print("13_student_certificates_school.png")

        # 14. Student exams
        page.goto(f"{BASE}/student/exams", wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=f"{SHOT_DIR}/14_student_exams.png", full_page=False)
        print("14_student_exams.png")

        # 15. AI chatbot - open chat window
        page.goto(f"{BASE}/student/certificates", wait_until="networkidle")
        time.sleep(1)
        try:
            page.wait_for_selector("#chat-toggle-btn", timeout=5000)
            page.click("#chat-toggle-btn")
            time.sleep(1)
            page.screenshot(path=f"{SHOT_DIR}/15_ai_chatbot.png", full_page=False)
            print("15_ai_chatbot.png")
        except Exception as e:
            print(f"15_ai_chatbot.png (chat toggle error: {e})")
            page.screenshot(path=f"{SHOT_DIR}/15_ai_chatbot.png", full_page=False)

        browser.close()
        print("\nAll screenshots done!")


if __name__ == "__main__":
    take_screenshots()
