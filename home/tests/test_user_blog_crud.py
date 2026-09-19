from django.test import TestCase
from home.models import UserBlogPage

class UserBlogPageCRUDTests(TestCase):
    def test_create_blog(self):
        blog = UserBlogPage.objects.create(name='Test User', title='My Test Blog', description='Hello World')
        
        self.assertEqual(UserBlogPage.objects.count(), 1)
        self.assertEqual(blog.title, 'My Test Blog')

    def test_read_blog(self):
        UserBlogPage.objects.create(name='Test User', title='Readable Blog', description='This is a test blog')

        response = self.client.get('/blogpage/')    

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Readable Blog')

    def test_update_blog(self):
        blog = UserBlogPage.objects.create(name='Old User', title='Old Title', description='Old Description')

        response = self.client.post('/edit_blogpage/%d/'%blog.id, {'name': 'Updated User', 'title': 'Updated Title', 'description': 'Updated Description'})

        self.assertEqual(response.status_code, 302)

        blog.refresh_from_db()

        self.assertEqual(blog.name, 'Updated User')
        self.assertEqual(blog.title, 'Updated Title')
        self.assertEqual(blog.description, 'Updated Description')

    def test_delete_blog(self):
        blog = UserBlogPage.objects.create(name='Delete User', title='Delete Title', description='This will be deleted')
        blog_id = blog.id

        response = self.client.post('/blogpage/delete/%d'%blog_id)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserBlogPage.objects.filter(id=blog_id).exists())