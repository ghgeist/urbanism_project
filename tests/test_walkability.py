"""
Lightweight smoke tests for core walkability service functions.
These tests use mocks to avoid requiring a live database connection.
"""
import pytest
from unittest.mock import Mock, patch
import geopandas as gpd
from shapely.geometry import Point
from services import walkability as walkability_module
from services.walkability import (
    miles_to_degrees,
    get_location,
    get_walkability_data,
    query_walkability_by_coords,
    validate_location_input,
    validate_buffer_size,
    _geocode_census,
    _normalize_us_street_spelling,
)


@pytest.fixture(autouse=True)
def _reset_was_cache():
    """Reset the module-level WAS-availability cache between tests to avoid pollution."""
    walkability_module._was_table_available = None
    yield
    walkability_module._was_table_available = None


class TestInputValidation:
    """Test input validation functions."""
    
    def test_validate_location_input_valid(self):
        """Test valid location inputs."""
        is_valid, error = validate_location_input("Knoxville, TN")
        assert is_valid is True
        assert error is None
    
    def test_validate_location_input_empty(self):
        """Test empty location input."""
        is_valid, error = validate_location_input("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_location_input_none(self):
        """Test None location input."""
        is_valid, error = validate_location_input(None)
        assert is_valid is False
    
    def test_validate_location_input_too_long(self):
        """Test location input that's too long."""
        long_string = "A" * 201
        is_valid, error = validate_location_input(long_string)
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_validate_buffer_size_valid(self):
        """Test valid buffer sizes."""
        is_valid, error = validate_buffer_size(1.0)
        assert is_valid is True
        assert error is None
        
        is_valid, error = validate_buffer_size(10)
        assert is_valid is True
    
    def test_validate_buffer_size_negative(self):
        """Test negative buffer size."""
        is_valid, error = validate_buffer_size(-1.0)
        assert is_valid is False
        assert "positive" in error.lower()
    
    def test_validate_buffer_size_zero(self):
        """Test zero buffer size."""
        is_valid, error = validate_buffer_size(0)
        assert is_valid is False
    
    def test_validate_buffer_size_too_large(self):
        """Test buffer size that's too large."""
        is_valid, error = validate_buffer_size(100)
        assert is_valid is False
        assert "too large" in error.lower()
    
    def test_validate_buffer_size_invalid_type(self):
        """Test buffer size with invalid type."""
        is_valid, error = validate_buffer_size("not a number")
        assert is_valid is False
        assert "number" in error.lower()


class TestNormalizeUsStreetSpelling:
    """Test UK→US spelling normalization for geocoding."""
    
    def test_normalizes_harbour_to_harbor(self):
        """Normalize 'harbour' to 'harbor'."""
        assert _normalize_us_street_spelling("1 Harbour Way") == "1 Harbor Way"
        assert _normalize_us_street_spelling("Harbour Street") == "Harbor Street"
    
    def test_normalizes_centre_to_center(self):
        """Normalize 'centre' to 'center'."""
        assert _normalize_us_street_spelling("City Centre") == "City Center"
        assert _normalize_us_street_spelling("Town Centre") == "Town Center"
    
    def test_normalizes_multiple_variants(self):
        """Normalize multiple UK spellings in one string."""
        result = _normalize_us_street_spelling("Harbour Centre, Favour Street")
        assert result == "Harbor Center, Favor Street"
    
    def test_case_insensitive(self):
        """Normalization is case-insensitive."""
        assert _normalize_us_street_spelling("HARBOUR") == "HARBOR"
        assert _normalize_us_street_spelling("Harbour") == "Harbor"
        assert _normalize_us_street_spelling("harbour") == "harbor"
    
    def test_whole_word_only(self):
        """Only replaces whole words, not substrings."""
        assert _normalize_us_street_spelling("harbouring") == "harbouring"  # not "harboring"
        assert _normalize_us_street_spelling("harbourite") == "harbourite"  # not "harborite"
    
    def test_handles_none_and_empty(self):
        """Returns None/empty unchanged."""
        assert _normalize_us_street_spelling(None) is None
        assert _normalize_us_street_spelling("") == ""
    
    def test_handles_non_string(self):
        """Returns non-string input unchanged."""
        assert _normalize_us_street_spelling(123) == 123
        assert _normalize_us_street_spelling([]) == []
    
    def test_preserves_unmatched_strings(self):
        """Strings without UK spellings are unchanged."""
        assert _normalize_us_street_spelling("123 Main St, Boston, MA") == "123 Main St, Boston, MA"
        assert _normalize_us_street_spelling("Normal Street Name") == "Normal Street Name"


class TestMilesToDegrees:
    """Test distance conversion logic."""
    
    def test_miles_to_degrees_at_equator(self):
        """Verify conversion at equator (latitude ~0)."""
        lat_deg, lon_deg = miles_to_degrees(69.0, 0.0)
        assert abs(lat_deg - 1.0) < 0.01  # ~1 degree latitude per 69 miles
        assert abs(lon_deg - 1.0) < 0.01
    
    def test_miles_to_degrees_at_mid_latitude(self):
        """Verify conversion at mid-latitude (e.g., Knoxville ~36°N)."""
        lat_deg, lon_deg = miles_to_degrees(69.0, 36.0)
        assert abs(lat_deg - 1.0) < 0.01
        # Longitude should be larger (more miles per degree) at higher latitude
        assert lon_deg > lat_deg


class TestGeocoding:
    """Test geocoding with mocked Nominatim."""

    def setup_method(self):
        """Clear the lru_cache between tests."""
        get_location.cache_clear()

    @patch('services.walkability._geocode_nominatim')
    def test_get_location_success(self, mock_geocode):
        """Test successful geocoding."""
        mock_location = Mock()
        mock_location.longitude = -83.9207
        mock_location.latitude = 35.9606
        mock_geocode.return_value = mock_location

        result = get_location("Knoxville, TN")
        assert result == (-83.9207, 35.9606)

    @patch('services.walkability._geocode_census')
    @patch('services.walkability._geocode_nominatim')
    def test_get_location_not_found(self, mock_nominatim, mock_census):
        """Test geocoding failure returns None when both geocoders find nothing."""
        mock_nominatim.return_value = None
        mock_census.return_value = None

        result = get_location("Nonexistent City, XX")
        assert result is None

    @patch('services.walkability._geocode_nominatim')
    def test_get_location_fallback_us_spelling(self, mock_geocode):
        """When as-is fails, retry with US street spelling (e.g. harbour→harbor) returns coords."""
        mock_location = Mock()
        mock_location.longitude = -89.0
        mock_location.latitude = 40.0
        # First call (raw with "harbour") returns None; second (normalized "harbor") succeeds.
        mock_geocode.side_effect = [None, mock_location]

        result = get_location("1 Example Harbour Way, Springfield, IL")
        assert result == (-89.0, 40.0)
        assert mock_geocode.call_count == 2

    @patch('services.walkability._geocode_census')
    @patch('services.walkability._geocode_nominatim')
    def test_get_location_census_fallback_on_nominatim_miss(self, mock_nominatim, mock_census):
        """When Nominatim returns None, Census geocoder is tried and returns coords."""
        mock_nominatim.return_value = None
        mock_census.return_value = (-71.0589, 42.3601)  # Boston coords

        result = get_location("123 Main St, Boston, MA 02101")
        assert result == (-71.0589, 42.3601)
        mock_census.assert_called_once_with("123 Main St, Boston, MA 02101")

    @patch('services.walkability._geocode_census')
    @patch('services.walkability._geocode_nominatim')
    def test_get_location_nominatim_wins_census_not_called(self, mock_nominatim, mock_census):
        """When Nominatim succeeds, Census geocoder is never called."""
        mock_location = Mock()
        mock_location.longitude = -83.9207
        mock_location.latitude = 35.9606
        mock_nominatim.return_value = mock_location

        result = get_location("Knoxville, TN")
        assert result == (-83.9207, 35.9606)
        mock_census.assert_not_called()

    @patch('services.walkability._geocode_census')
    @patch('services.walkability._geocode_nominatim')
    def test_get_location_both_geocoders_fail(self, mock_nominatim, mock_census):
        """When both geocoders return None, get_location returns None."""
        mock_nominatim.return_value = None
        mock_census.return_value = None

        result = get_location("Completely Nonexistent Place XYZ")
        assert result is None

    @patch('services.walkability._census_urlopen')
    def test_geocode_census_success(self, mock_urlopen):
        """Census geocoder parses coordinates from a successful API response."""
        import json
        payload = {
            "result": {
                "addressMatches": [
                    {"coordinates": {"x": -77.0366, "y": 38.8971}}
                ]
            }
        }
        mock_urlopen.return_value = json.dumps(payload).encode()

        result = _geocode_census("1600 Pennsylvania Ave NW, Washington, DC 20500")
        assert result == (-77.0366, 38.8971)

    @patch('services.walkability._census_urlopen')
    def test_geocode_census_no_matches(self, mock_urlopen):
        """Census geocoder returns None when API finds no address matches."""
        import json
        payload = {"result": {"addressMatches": []}}
        mock_urlopen.return_value = json.dumps(payload).encode()

        result = _geocode_census("9999 Fake Street, Nowhere, ZZ 00000")
        assert result is None

    @patch('services.walkability._census_urlopen')
    def test_geocode_census_network_error(self, mock_urlopen):
        """Census geocoder returns None gracefully after network error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

        result = _geocode_census("123 Main St, Boston, MA 02101")
        assert result is None

    @patch('services.walkability._census_urlopen')
    def test_geocode_census_invalid_json(self, mock_urlopen):
        """Census geocoder returns None gracefully when response is not valid JSON."""
        mock_urlopen.return_value = b"not json"

        result = _geocode_census("123 Main St, Boston, MA 02101")
        assert result is None


class TestWalkabilityData:
    """Test data fetching with mocked database."""
    
    def test_get_walkability_data_returns_gdf(self):
        """Verify function returns GeoDataFrame with expected columns."""
        with patch('services.walkability.get_location', return_value=(-83.9207, 35.9606)):
            with patch('services.walkability.get_db_connection') as mock_db:
                # Mock database connection and cursor with proper context manager
                mock_conn = Mock()
                mock_cursor = Mock()
                
                # Set up context manager for cursor
                mock_cursor.__enter__ = Mock(return_value=mock_cursor)
                mock_cursor.__exit__ = Mock(return_value=None)
                mock_conn.cursor.return_value = mock_cursor

                # Probe call runs first; return False so main query omits the WAS JOIN.
                mock_cursor.fetchone.return_value = (False,)
                mock_cursor.description = [
                    ('geoid20',), ('d2a_ranked',), ('d2b_ranked',), 
                    ('d3b_ranked',), ('d4a_ranked',), ('natwalkind',), ('geometry',), ('dist_miles',)
                ]
                from shapely import wkb
                mock_point = Point(-83.9207, 35.9606).buffer(0.01)
                mock_cursor.fetchall.return_value = [
                    ('123456789012', 10, 12, 8, 15, 11.25, wkb.dumps(mock_point), 0.0)
                ]
                
                mock_db.return_value = mock_conn
                
                result = get_walkability_data("Knoxville, TN", 1.0, conn=None)
                
                assert isinstance(result, gpd.GeoDataFrame)
                assert 'geoid20' in result.columns
                assert 'natwalkind' in result.columns
                assert result.crs == 'EPSG:4326'
    
    def test_get_walkability_data_handles_memoryview(self):
        """Verify function correctly converts memoryview objects from psycopg2."""
        # This test ensures we never regress on the memoryview conversion issue
        # that occurs when using direct psycopg2 connections in production
        with patch('services.walkability.get_location', return_value=(-83.9207, 35.9606)):
            with patch('services.walkability.get_db_connection') as mock_db:
                mock_conn = Mock()
                mock_cursor = Mock()
                
                # Set up context manager for cursor
                mock_cursor.__enter__ = Mock(return_value=mock_cursor)
                mock_cursor.__exit__ = Mock(return_value=None)
                mock_conn.cursor.return_value = mock_cursor

                mock_cursor.fetchone.return_value = (False,)
                mock_cursor.description = [
                    ('geoid20',), ('d2a_ranked',), ('d2b_ranked',), 
                    ('d3b_ranked',), ('d4a_ranked',), ('natwalkind',), ('geometry',), ('dist_miles',)
                ]
                from shapely import wkb
                mock_point = Point(-83.9207, 35.9606).buffer(0.01)
                wkb_bytes = wkb.dumps(mock_point)
                
                # Simulate psycopg2 returning memoryview objects
                # (psycopg2 returns memoryview for binary data)
                memoryview_obj = memoryview(wkb_bytes)
                mock_cursor.fetchall.return_value = [
                    ('123456789012', 10, 12, 8, 15, 11.25, memoryview_obj, 0.0)
                ]
                
                mock_db.return_value = mock_conn
                
                # This should not raise TypeError: Expected bytes or string, got memoryview
                result = get_walkability_data("Knoxville, TN", 1.0, conn=None)
                
                assert isinstance(result, gpd.GeoDataFrame)
                assert 'geoid20' in result.columns
                assert 'natwalkind' in result.columns
                assert result.crs == 'EPSG:4326'
                # Verify geometry was correctly converted
                assert len(result) == 1
                assert result.geometry.iloc[0] is not None

    def test_query_walkability_by_coords_includes_dist_miles(self):
        """Verify coordinate query returns GeoDataFrame with dist_miles column."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor

        # Probe query runs first (returns [True]), then main query's fetchall.
        mock_cursor.fetchone.return_value = (True,)
        mock_cursor.description = [
            ('geoid20',), ('d2a_ranked',), ('d2b_ranked',),
            ('d3b_ranked',), ('d4a_ranked',), ('natwalkind',), ('was_2019',),
            ('geometry',), ('dist_miles',)
        ]
        from shapely import wkb
        mock_poly = Point(-83.9207, 35.9606).buffer(0.01)
        mock_cursor.fetchall.return_value = [
            ('123456789012', 10, 12, 8, 15, 11.25, 17.5, wkb.dumps(mock_poly), 0.25)
        ]

        result = query_walkability_by_coords(-83.9207, 35.9606, 2.0, conn=mock_conn)

        assert isinstance(result, gpd.GeoDataFrame)
        assert 'dist_miles' in result.columns
        assert 'was_2019' in result.columns
        assert result['dist_miles'].iloc[0] == 0.25
        assert result['was_2019'].iloc[0] == 17.5
        # The last execute call is the main query; assert its shape.
        last_sql = mock_cursor.execute.call_args.args[0]
        last_params = mock_cursor.execute.call_args.args[1]
        assert "LEFT JOIN walkable_accessibility_score" in last_sql
        assert "was.was_2019" in last_sql
        assert len(last_params) == 8

    def test_query_falls_back_to_nwi_only_when_was_table_missing(self):
        """If the WAS table probe returns False, query uses NWI-only SQL."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor

        # Probe returns False; main query runs without the JOIN.
        mock_cursor.fetchone.return_value = (False,)
        mock_cursor.description = [
            ('geoid20',), ('d2a_ranked',), ('d2b_ranked',),
            ('d3b_ranked',), ('d4a_ranked',), ('natwalkind',), ('geometry',), ('dist_miles',)
        ]
        from shapely import wkb
        mock_poly = Point(-83.9207, 35.9606).buffer(0.01)
        mock_cursor.fetchall.return_value = [
            ('123456789012', 10, 12, 8, 15, 11.25, wkb.dumps(mock_poly), 0.25)
        ]

        result = query_walkability_by_coords(-83.9207, 35.9606, 2.0, conn=mock_conn)

        assert isinstance(result, gpd.GeoDataFrame)
        assert 'was_2019' not in result.columns
        # Last execute call is the NWI-only main query; it must not JOIN.
        last_sql = mock_cursor.execute.call_args.args[0]
        assert "LEFT JOIN walkable_accessibility_score" not in last_sql
        assert "FROM national_walkability_index" in last_sql


class TestWalkabilityDataConnectionCheck:
    """Test that get_walkability_data checks connection before use."""

    @patch('services.walkability.get_location', return_value=(-83.9207, 35.9606))
    def test_get_walkability_data_raises_on_closed_connection(self, mock_get_location):
        """Test that get_walkability_data raises InterfaceError for closed connection."""
        import psycopg2
        closed_conn = Mock()
        closed_conn.closed = True

        with pytest.raises(psycopg2.InterfaceError) as exc_info:
            get_walkability_data("Knoxville, TN", 1.0, conn=closed_conn)

        assert "Connection is closed" in str(exc_info.value)

    @patch('services.walkability.get_location', return_value=(-83.9207, 35.9606))
    def test_get_walkability_data_succeeds_with_open_connection(self, mock_get_location):
        """Test that get_walkability_data works with open connection."""
        from shapely import wkb
        open_conn = Mock()
        open_conn.closed = False

        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        open_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = (False,)
        mock_cursor.description = [
            ('geoid20',), ('d2a_ranked',), ('d2b_ranked',),
            ('d3b_ranked',), ('d4a_ranked',), ('natwalkind',), ('geometry',), ('dist_miles',)
        ]
        mock_point = Point(-83.9207, 35.9606).buffer(0.01)
        mock_cursor.fetchall.return_value = [
            ('123456789012', 10, 12, 8, 15, 11.25, wkb.dumps(mock_point), 0.0)
        ]

        result = get_walkability_data("Knoxville, TN", 1.0, conn=open_conn)

        assert isinstance(result, gpd.GeoDataFrame)
        assert 'geoid20' in result.columns
        assert 'natwalkind' in result.columns
