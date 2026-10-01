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
        app.sidebar.radio[0].set_value("4 · Onde investigar oportunidades").run()
        app.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[-1].value, "0")

    def test_empty_year_filter_has_a_helpful_message(self):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        app.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Escolha ao menos", app.info[0].value)

    def test_fifteen_questions_are_visible(self):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        app.sidebar.radio[0].set_value("6 · Respostas às 15 perguntas").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.subheader), 15)
        self.assertFalse(any("Sem Informação lidera" in element.value for element in app.markdown))

    def test_future_scenarios_are_explicitly_not_ml_forecasts(self):
        app = AppTest.from_file(str(APP),default_timeout=40).run()
        app.sidebar.radio[0].set_value("5 · O que esperar do futuro").run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any("Cenários qualitativos" in element.value for element in app.caption))
        self.assertTrue(any("IEA" in element.value for element in app.markdown))

    def test_year_and_technology_filters_render(self):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        app.multiselect[0].set_value([2024,2025]).run()
        app.multiselect[1].set_value(["BEV"]).run()
        app.selectbox[1].set_value(12).run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("12 meses", app.success[0].value)

    def test_single_month_ranking_and_empty_city_filter(self):
        app = AppTest.from_file(str(APP),default_timeout=40).run()
        app.sidebar.radio[0].set_value("3 · Quem lidera as vendas").run()
        app.select_slider[0].set_value((1,1)).run()
        self.assertEqual(len(app.exception),0)
        app.sidebar.radio[0].set_value("2 · Onde a adoção avança").run()
        app.number_input[0].set_value(100000000).run()
        self.assertEqual(len(app.exception),0)


if __name__ == "__main__":
    unittest.main()
