"""Testo regras do mapa sem consultar a rede ou o banco."""

import copy
import unittest

from src.transformation.osm_charging_to_silver import transform


def sample():
    return {"portfolio_metadata": {"license": "ODbL-1.0", "captured_at_utc": "2026-09-30T12:00:00+00:00"},
            "elements": [{"type": "node", "id": 1, "lat": -23.5, "lon": -46.6,
                          "tags": {"amenity": "charging_station", "socket:type2": "2"}}]}


class OSMTests(unittest.TestCase):
    def test_unknown_access_is_not_public(self):
        frame = transform(sample())
        self.assertEqual(frame.iloc[0]["acesso_classificado"], "nao_informado")
        self.assertIsNone(frame.iloc[0]["municipio_declarado"])

    def test_restricted_access_and_center(self):
        payload = sample()
        element = payload["elements"][0]
        element.update(type="way", center={"lat": -23.5, "lon": -46.6})
        element["tags"]["access"] = "customers"
        frame = transform(payload)
        self.assertTrue(frame.iloc[0]["coordenada_aproximada"])
        self.assertEqual(frame.iloc[0]["acesso_classificado"], "restrito_declarado")

    def test_duplicates_rejected(self):
        payload = sample()
        payload["elements"].append(copy.deepcopy(payload["elements"][0]))
        with self.assertRaises(ValueError):
            transform(payload)

    def test_partial_response_rejected(self):
        payload = sample()
        payload["remark"] = "runtime error: Query timed out"
        with self.assertRaises(ValueError):
            transform(payload)

    def test_invalid_coordinates_rejected(self):
        payload = sample()
        payload["elements"][0]["lat"] = 95
        with self.assertRaises(ValueError):
            transform(payload)


if __name__ == "__main__":
    unittest.main()
