"""
Tests for database connection caching and error recovery.
These tests ensure that closed connections are detected and handled gracefully,
preventing the "connection already closed" error in production.
"""
import pytest
from unittest.mock import Mock, patch
import psycopg2
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkb

# Import the functions we're testing
from components.map_display import (
    _is_connection_closed,
    get_cached_db_connection,
    cached_get_walkability_data,
    cached_get_profile,
)
from services.walkability import get_walkability_data


class TestConnectionClosedDetection:
    """Test the _is_connection_closed helper function."""
    
    def test_is_connection_closed_none(self):
        """Test that None connection is detected as closed."""
        assert _is_connection_closed(None) is True
    
    def test_is_connection_closed_psycopg2_open(self):
        """Test that open psycopg2 connection is detected as open."""
        mock_conn = Mock()
        mock_conn.closed = False
        assert _is_connection_closed(mock_conn) is False
    
    def test_is_connection_closed_psycopg2_closed(self):
        """Test that closed psycopg2 connection is detected as closed."""
        mock_conn = Mock()
        mock_conn.closed = True
        assert _is_connection_closed(mock_conn) is True
    
    def test_is_connection_closed_missing_attr(self):
        """Test that connection without 'closed' attribute returns False."""
        mock_conn = Mock(spec=[])  # no attributes
        assert _is_connection_closed(mock_conn) is False


class TestCachedConnection:
    """Test the get_cached_db_connection caching behavior."""
    
    @patch('components.map_display.get_db_connection')
    def test_get_cached_db_connection_creates_connection(self, mock_get_db):
        """Test that a new connection is created when cache is empty."""
        mock_conn = Mock()
        mock_conn.closed = False
        mock_get_db.return_value = mock_conn

        # Clear cache first
        get_cached_db_connection.clear()

        conn = get_cached_db_connection()

        assert conn == mock_conn
        mock_get_db.assert_called_once()
    
    @patch('components.map_display.get_db_connection')
    def test_get_cached_db_connection_reuses_cached(self, mock_get_db):
        """Test that cached connection is reused on subsequent calls."""
        mock_conn = Mock()
        mock_conn.closed = False
        mock_get_db.return_value = mock_conn

        # Clear cache first
        get_cached_db_connection.clear()

        # First call creates connection
        conn1 = get_cached_db_connection()
        # Second call should reuse cached connection
        conn2 = get_cached_db_connection()

        assert conn1 == conn2
        # Should only be called once due to caching
        assert mock_get_db.call_count == 1


class TestCachedWalkabilityDataWithClosedConnection:
    """Test cached_get_walkability_data handling of closed connections."""
    
    def setup_method(self):
        """Clear caches before each test."""
        get_cached_db_connection.clear()
        cached_get_walkability_data.clear()
        cached_get_profile.clear()
    
    def test_closed_connection_clears_cache_and_retries(self):
        """Test that closed connection triggers cache clear and retry."""
        # First connection is closed
        closed_conn = Mock()
        closed_conn.closed = True
        
        # Second connection (after cache clear) is open
        open_conn = Mock()
        open_conn.closed = False
        
        # Mock GeoDataFrame result
        mock_gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')
        
        # Patch the actual function calls inside the cached function
        with patch('components.map_display.get_cached_db_connection', side_effect=[closed_conn, open_conn]):
            with patch('components.map_display.get_walkability_data', return_value=mock_gdf) as mock_get_data:
                result = cached_get_walkability_data("Knoxville, TN", 1.0)
                
                # Should have called get_walkability_data with the open connection
                mock_get_data.assert_called_once_with("Knoxville, TN", 1.0, open_conn)
                assert isinstance(result, gpd.GeoDataFrame)

    def test_interface_error_triggers_retry(self):
        """Test that InterfaceError triggers cache clear and retry."""
        bad_conn = Mock()
        bad_conn.closed = False
        good_conn = Mock()
        good_conn.closed = False

        mock_gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')

        with patch('components.map_display.get_cached_db_connection', side_effect=[bad_conn, good_conn]):
            with patch('components.map_display.get_walkability_data', side_effect=[
                psycopg2.InterfaceError("connection already closed"),
                mock_gdf
            ]) as mock_get_data:
                result = cached_get_walkability_data("Knoxville, TN", 1.0)
                assert mock_get_data.call_count == 2
                assert isinstance(result, gpd.GeoDataFrame)

    def test_operational_error_triggers_retry(self):
        """Test that OperationalError triggers cache clear and retry."""
        bad_conn = Mock()
        bad_conn.closed = False
        good_conn = Mock()
        good_conn.closed = False

        mock_gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')

        with patch('components.map_display.get_cached_db_connection', side_effect=[bad_conn, good_conn]):
            with patch('components.map_display.get_walkability_data', side_effect=[
                psycopg2.OperationalError("server closed the connection"),
                mock_gdf
            ]) as mock_get_data:
                result = cached_get_walkability_data("Knoxville, TN", 1.0)
                assert mock_get_data.call_count == 2
                assert isinstance(result, gpd.GeoDataFrame)

    def test_retry_failure_raises_original_error(self):
        """Test that if retry also fails, original error is raised."""
        bad_conn = Mock()
        bad_conn.closed = False
        also_bad_conn = Mock()
        also_bad_conn.closed = False

        original_error = psycopg2.InterfaceError("connection already closed")
        retry_error = psycopg2.OperationalError("connection failed")

        with patch('components.map_display.get_cached_db_connection', side_effect=[bad_conn, also_bad_conn]):
            with patch('components.map_display.get_walkability_data', side_effect=[original_error, retry_error]):
                with pytest.raises(psycopg2.InterfaceError) as exc_info:
                    cached_get_walkability_data("Knoxville, TN", 1.0)
                assert str(exc_info.value) == "connection already closed"

    def test_successful_query_with_open_connection(self):
        """Test normal successful flow with open connection."""
        open_conn = Mock()
        open_conn.closed = False

        mock_gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')

        with patch('components.map_display.get_cached_db_connection', return_value=open_conn):
            with patch('components.map_display.get_walkability_data', return_value=mock_gdf) as mock_get_data:
                result = cached_get_walkability_data("Knoxville, TN", 1.0)
                mock_get_data.assert_called_once_with("Knoxville, TN", 1.0, open_conn)
                assert isinstance(result, gpd.GeoDataFrame)


class TestCachedGetProfile:
    """Test profile cache layer (single query + split + compute)."""

    def setup_method(self):
        get_cached_db_connection.clear()
        cached_get_walkability_data.clear()
        cached_get_profile.clear()

    def test_cached_get_profile_none_on_geocode_failure(self):
        with patch('components.map_display.cached_get_location', return_value=None):
            result = cached_get_profile("Nowhere, ZZ", 1.0, 3.0, 2.0)
            assert result is None

    def test_cached_get_profile_invalid_radius_relation_raises(self):
        with pytest.raises(ValueError, match="Search radius must be greater than buffer radius"):
            cached_get_profile("Knoxville, TN", 2.0, 2.0, 2.0)

    def test_cached_get_profile_single_query_and_split(self):
        open_conn = Mock()
        open_conn.closed = False
        full_gdf = gpd.GeoDataFrame({
            'geoid20': ['A', 'B', 'C'],
            'natwalkind': [11.0, 14.0, 18.0],
            'd4a_ranked': [10.0, 14.0, 18.0],
            'dist_miles': [0.4, 1.0, 2.5],
            'geometry': [
                Point(-83.92, 35.96).buffer(0.01),
                Point(-83.93, 35.97).buffer(0.01),
                Point(-83.94, 35.98).buffer(0.01),
            ],
        }, crs='EPSG:4326')

        computed_profile = {
            "everyday_convenience": 12.5,
            "transit_viability": 12.0,
            "variation": 2.12,
            "upgrade_potential": {"found": True, "candidates": []},
            "walkable_island": {"is_island": False, "label": None},
        }

        with patch('components.map_display.cached_get_location', return_value=(-83.92, 35.96)):
            with patch('components.map_display.get_cached_db_connection', return_value=open_conn):
                with patch('components.map_display.query_walkability_by_coords', return_value=full_gdf) as mock_query:
                    with patch('components.map_display.compute_full_profile', return_value=computed_profile) as mock_profile:
                        result = cached_get_profile("Knoxville, TN", 1.0, 3.0, 2.0)

                        mock_query.assert_called_once_with(-83.92, 35.96, 3.0, open_conn)
                        selected_arg = mock_profile.call_args.kwargs["selected_gdf"]
                        context_arg = mock_profile.call_args.kwargs["context_gdf"]
                        assert len(selected_arg) == 2
                        assert len(context_arg) == 3
                        assert result["location"] == (-83.92, 35.96)
                        assert len(result["selected_gdf"]) == 2

    def test_cached_get_profile_retries_on_interface_error(self):
        bad_conn = Mock()
        bad_conn.closed = False
        good_conn = Mock()
        good_conn.closed = False

        full_gdf = gpd.GeoDataFrame({
            'geoid20': ['A'],
            'natwalkind': [11.0],
            'd4a_ranked': [10.0],
            'dist_miles': [0.4],
            'geometry': [Point(-83.92, 35.96).buffer(0.01)],
        }, crs='EPSG:4326')

        with patch('components.map_display.cached_get_location', return_value=(-83.92, 35.96)):
            with patch('components.map_display.get_cached_db_connection', side_effect=[bad_conn, good_conn]):
                with patch('components.map_display.query_walkability_by_coords', side_effect=[
                    psycopg2.InterfaceError("connection closed"),
                    full_gdf,
                ]) as mock_query:
                    with patch('components.map_display.compute_full_profile', return_value={}):
                        result = cached_get_profile("Knoxville, TN", 0.5, 2.0, 2.0)
                        assert mock_query.call_count == 2
                        assert result["location"] == (-83.92, 35.96)


class TestWalkabilityDataConnectionCheck:
    """Test that get_walkability_data checks connection before use."""
    
    @patch('services.walkability.get_location', return_value=(-83.9207, 35.9606))
    def test_get_walkability_data_raises_on_closed_connection(self, mock_get_location):
        """Test that get_walkability_data raises InterfaceError for closed connection."""
        closed_conn = Mock()
        closed_conn.closed = True

        with pytest.raises(psycopg2.InterfaceError) as exc_info:
            get_walkability_data("Knoxville, TN", 1.0, conn=closed_conn)
        
        assert "Connection is closed" in str(exc_info.value)
    
    @patch('services.walkability.get_location', return_value=(-83.9207, 35.9606))
    def test_get_walkability_data_succeeds_with_open_connection(self, mock_get_location):
        """Test that get_walkability_data works with open connection."""
        open_conn = Mock()
        open_conn.closed = False

        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        open_conn.cursor.return_value = mock_cursor
        
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
