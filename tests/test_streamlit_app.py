"""Confiro as páginas da prévia com os exports reais, sem iniciar o banco."""

from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


class DashboardTests(unittest.TestCase):
    def test_every_page_renders_without_exception(self):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "1.266.671")
        for page in app.sidebar.radio[0].options:
            with self.subTest(page=page):
                app.sidebar.radio[0].set_value(page).run()
                self.assertEqual(len(app.exception), 0, str(app.exception))

    def test_historical_stock_is_not_sum_of_months(self):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        app.selectbox[0].set_value("2024-01").run()
        self.assertEqual(app.metric[0].value, "304.546")

    def test_empty_map_filter_is_supported(self):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        app.sidebar.radio[0].set_value("Recarga e rede elétrica").run()
        app.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "0")


if __name__ == "__main__":
    unittest.main()
