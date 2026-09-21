from django.test import SimpleTestCase
from utils.sanitizer import clean_html

class SanitizerTests(SimpleTestCase):
    def test_clean_html_removes_unsafe_html(self):
        dirty_html = '''
            <script>alert(1)</script>
            <b>Hello</b>
            <a href="https://example.com" onclick="evil()">Link</a>
        '''

        cleaned_html = clean_html(dirty_html)

        self.assertNotIn('<script', cleaned_html)
        self.assertNotIn('onclick', cleaned_html)

        self.assertIn('<b>Hello</b>', cleaned_html)
        self.assertIn('href="https://example.com"', cleaned_html)