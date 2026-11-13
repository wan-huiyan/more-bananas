"""The page still builds, with the drawn tab icon, when the installed icon picture is missing."""
import unittest

from test_podium import page_for


class TabIconTests(unittest.TestCase):
    def test_the_installed_icon_picture_is_used(self):
        page = page_for({'Slack': 0.4})
        self.assertIn('href="data:image/png;base64,AA=="', page)

    def test_a_missing_icon_picture_falls_back_to_the_drawn_icon(self):
        page = page_for({'Slack': 0.4}, icon=False)
        self.assertNotIn('data:image/png;base64,', page)
        self.assertIn("<link rel=icon href='data:image/svg+xml,", page)


if __name__ == '__main__':
    unittest.main()
