import unittest
from unittest.mock import patch
from scripts.walkability import get_location, Location
from geopy.exc import GeocoderUnavailable

class TestWalkability(unittest.TestCase):

    @patch('scripts.walkability.Nominatim')
    def test_get_location_success(self, MockNominatim):
        # Mock the geocode method to return a mock location
        mock_geolocator = MockNominatim.return_value
        mock_geolocator.geocode.return_value = type('Location', (object,), {'longitude': -83.9207, 'latitude': 35.9606})()

        location_string = "Knoxville"
        result = get_location(location_string)

        self.assertIsNotNone(result)
        self.assertEqual(result.longitude, -83.9207)
        self.assertEqual(result.latitude, 35.9606)

    @patch('scripts.walkability.Nominatim')
    def test_get_location_not_found(self, MockNominatim):
        # Mock the geocode method to return None
        mock_geolocator = MockNominatim.return_value
        mock_geolocator.geocode.return_value = None

        location_string = "UnknownPlace"
        result = get_location(location_string)

        self.assertIsNone(result)

    @patch('scripts.walkability.Nominatim')
    def test_get_location_geocoder_unavailable(self, MockNominatim):
        # Mock the geocode method to raise GeocoderUnavailable
        mock_geolocator = MockNominatim.return_value
        mock_geolocator.geocode.side_effect = GeocoderUnavailable

        location_string = "Knoxville"
        result = get_location(location_string)

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()