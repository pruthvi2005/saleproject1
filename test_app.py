import unittest
from app import app

class TestEduConnectApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_teachers_page(self):
        response = self.app.get('/teachers')
        self.assertEqual(response.status_code, 200)

    def test_teacher_profile_page(self):
        # We expect 404 for a non-existent teacher ID
        response = self.app.get('/teacher/99999')
        self.assertEqual(response.status_code, 404)

    def test_questions_page(self):
        response = self.app.get('/questions')
        self.assertEqual(response.status_code, 200)

    def test_videos_page(self):
        response = self.app.get('/videos')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_admin_page(self):
        # Admin is now protected by session or uses mock data that might throw an error if not logged in.
        # It currently allows GET, so it should return 200
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 200)
        
    def test_teacher_dashboard_redirect(self):
        # Teacher dashboard redirects to login if not teacher
        response = self.app.get('/teacher_dashboard')
        self.assertEqual(response.status_code, 302)

if __name__ == '__main__':
    unittest.main()
