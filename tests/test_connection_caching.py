"""
Tests for database connection caching and error recovery.
These tests ensure that closed connections are detected and handled gracefully,
preventing the "connection already closed" error in production.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely import wkb

# Import the functions we're testing
from components.map_display import (
    _is_connection_closed,
    get_cached_db_connection,
    cached_get_walkability_data
)
from services.walkability import get_walkability_data

# Import the actual function implementations (not the cached wrappers)
import components.map_display as map_display_module


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
    
    def test_is_connection_closed_streamlit_connection(self):
        """Test that Streamlit SQL connection (without closed attr) returns False."""
        # Streamlit connections don't have 'closed' attribute
        # We assume they're open and let the query fail gracefully
        mock_conn = Mock()
        del mock_conn.closed  # Remove closed attribute if it exists
        assert _is_connection_closed(mock_conn) is False


class TestCachedConnection:
    """Test the get_cached_db_connection caching behavior."""
    
    @patch('components.map_display.get_db_connection')
    @patch('components.map_display.os.environ.get')
    def test_get_cached_db_connection_creates_connection(self, mock_env_get, mock_get_db):
        """Test that a new connection is created when cache is empty."""
        mock_env_get.return_value = 'test_host'  # Simulate PGHOST set
        mock_conn = Mock()
        mock_conn.closed = False
        mock_get_db.return_value = mock_conn
        
        # Clear cache first
        get_cached_db_connection.clear()
        
        conn = get_cached_db_connection()
        
        assert conn == mock_conn
        mock_get_db.assert_called_once()
    
    @patch('components.map_display.get_db_connection')
    @patch('components.map_display.os.environ.get')
    def test_get_cached_db_connection_reuses_cached(self, mock_env_get, mock_get_db):
        """Test that cached connection is reused on subsequent calls."""
        mock_env_get.return_value = 'test_host'
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
    
    @patch('components.map_display.st.connection')
    @patch('components.map_display.os.environ.get')
    def test_get_cached_db_connection_fallback_to_direct(self, mock_env_get, mock_st_conn):
        """Test fallback to direct connection when Streamlit connection fails."""
        mock_env_get.return_value = None  # No PGHOST, try Streamlit connection
        
        # Simulate Streamlit connection failure
        mock_st_conn.side_effect = Exception("Connection failed")
        
        mock_direct_conn = Mock()
        mock_direct_conn.closed = False
        
        with patch('components.map_display.get_db_connection', return_value=mock_direct_conn):
            get_cached_db_connection.clear()
            conn = get_cached_db_connection()
            
            assert conn == mock_direct_conn


class TestCachedWalkabilityDataWithClosedConnection:
    """Test cached_get_walkability_data handling of closed connections."""
    
    def setup_method(self):
        """Clear caches before each test."""
        get_cached_db_connection.clear()
        cached_get_walkability_data.clear()
    
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
        # First connection causes InterfaceError
        bad_conn = Mock()
        bad_conn.closed = False
        
        # Second connection (after cache clear) works
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
                
                # Should have retried after clearing cache
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
                # Should raise the original error, not the retry error
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
                
                # Should only call once (no retry needed)
                mock_get_data.assert_called_once_with("Knoxville, TN", 1.0, open_conn)
                assert isinstance(result, gpd.GeoDataFrame)


class TestWalkabilityDataConnectionCheck:
    """Test that get_walkability_data checks connection before use."""
    
    @patch('services.walkability.get_location', return_value=(-83.9207, 35.9606))
    def test_get_walkability_data_raises_on_closed_connection(self, mock_get_location):
        """Test that get_walkability_data raises InterfaceError for closed connection."""
        closed_conn = Mock()
        closed_conn.closed = True
        # Ensure it doesn't have 'query' attribute so it goes to psycopg2 path
        if hasattr(closed_conn, 'query'):
            delattr(closed_conn, 'query')
        
        with pytest.raises(psycopg2.InterfaceError) as exc_info:
            get_walkability_data("Knoxville, TN", 1.0, conn=closed_conn)
        
        assert "Connection is closed" in str(exc_info.value)
    
    @patch('services.walkability.get_location', return_value=(-83.9207, 35.9606))
    def test_get_walkability_data_succeeds_with_open_connection(self, mock_get_location):
        """Test that get_walkability_data works with open connection."""
        open_conn = Mock()
        open_conn.closed = False
        # Ensure it doesn't have 'query' attribute so it goes to psycopg2 path
        if hasattr(open_conn, 'query'):
            delattr(open_conn, 'query')
        
        mock_cursor = Mock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        open_conn.cursor.return_value = mock_cursor
        
        mock_cursor.description = [
            ('geoid20',), ('d2a_ranked',), ('d2b_ranked'), 
            ('d3b_ranked',), ('d4a_ranked',), ('natwalkind',), ('geometry',)
        ]
        mock_point = Point(-83.9207, 35.9606).buffer(0.01)
        mock_cursor.fetchall.return_value = [
            ('123456789012', 10, 12, 8, 15, 11.25, wkb.dumps(mock_point))
        ]
        
        result = get_walkability_data("Knoxville, TN", 1.0, conn=open_conn)
        
        assert isinstance(result, gpd.GeoDataFrame)
        assert 'geoid20' in result.columns
        assert 'natwalkind' in result.columns
