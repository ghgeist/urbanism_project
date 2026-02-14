"""
Lightweight smoke tests for core walkability service functions.
These tests use mocks to avoid requiring a live database connection.
"""
import pytest
from unittest.mock import Mock, patch
import geopandas as gpd
from shapely.geometry import Point
from services.walkability import (
    miles_to_degrees,
    calculate_zoom_level,
    get_location,
    get_walkability_data,
    query_walkability_by_coords,
    create_map,
    CHOROPLETH_COLORMAP,
    validate_location_input,
    validate_buffer_size
)


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


class TestZoomLevel:
    """Test map zoom calculation."""
    
    def test_zoom_level_small_buffer(self):
        """Small buffer should result in higher zoom."""
        zoom = calculate_zoom_level(0.5)
        assert zoom > 10
    
    def test_zoom_level_large_buffer(self):
        """Large buffer should result in lower zoom."""
        zoom = calculate_zoom_level(10.0)
        assert zoom < 14
    
    def test_zoom_level_monotonic(self):
        """Zoom should decrease as buffer increases."""
        zoom_small = calculate_zoom_level(0.5)
        zoom_large = calculate_zoom_level(5.0)
        assert zoom_small > zoom_large


class TestGeocoding:
    """Test geocoding with mocked Nominatim."""
    
    @patch('services.walkability.Nominatim')
    def test_get_location_success(self, mock_nominatim_class):
        """Test successful geocoding."""
        mock_location = Mock()
        mock_location.longitude = -83.9207
        mock_location.latitude = 35.9606
        
        mock_geolocator = Mock()
        mock_geolocator.geocode.return_value = mock_location
        mock_nominatim_class.return_value = mock_geolocator
        
        result = get_location("Knoxville, TN")
        assert result == (-83.9207, 35.9606)
    
    @patch('services.walkability.Nominatim')
    def test_get_location_not_found(self, mock_nominatim_class):
        """Test geocoding failure returns None."""
        mock_geolocator = Mock()
        mock_geolocator.geocode.return_value = None
        mock_nominatim_class.return_value = mock_geolocator
        
        result = get_location("Nonexistent City, XX")
        assert result is None


class TestWalkabilityData:
    """Test data fetching with mocked database."""
    
    def test_get_walkability_data_returns_gdf(self):
        """Verify function returns GeoDataFrame with expected columns."""
        # Create mock GeoDataFrame
        mock_gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'd2a_ranked': [10],
            'd2b_ranked': [12],
            'd3b_ranked': [8],
            'd4a_ranked': [15],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')
        
        with patch('services.walkability.get_location', return_value=(-83.9207, 35.9606)):
            with patch('services.walkability.get_db_connection') as mock_db:
                # Mock database connection and cursor with proper context manager
                mock_conn = Mock()
                mock_cursor = Mock()
                
                # Set up context manager for cursor
                mock_cursor.__enter__ = Mock(return_value=mock_cursor)
                mock_cursor.__exit__ = Mock(return_value=None)
                mock_conn.cursor.return_value = mock_cursor
                
                # Mock query result
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
                
                # Mock query result with memoryview objects (as psycopg2 returns)
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
        assert 'dist_miles' in result.columns
        assert result['dist_miles'].iloc[0] == 0.25


class TestMapCreation:
    """Test map creation logic."""
    
    def test_create_map_with_valid_data(self):
        """Test map creation with valid location and data."""
        location = (-83.9207, 35.9606)
        gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')
        
        m = create_map(location, gdf, buffer_size=1.0)
        assert m is not None
    
    def test_create_map_empty_data(self):
        """Test map creation with empty GeoDataFrame returns None."""
        location = (-83.9207, 35.9606)
        empty_gdf = gpd.GeoDataFrame(columns=['geoid20', 'natwalkind', 'geometry'], crs='EPSG:4326')
        
        m = create_map(location, empty_gdf, buffer_size=1.0)
        assert m is None
    
    def test_create_map_no_location(self):
        """Test map creation with None location returns None."""
        gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')
        
        m = create_map(None, gdf, buffer_size=1.0)
        assert m is None

    def test_choropleth_colormap_constant(self):
        assert CHOROPLETH_COLORMAP == "Blues"

    def test_create_map_uses_colormap_constant(self):
        location = (-83.9207, 35.9606)
        gdf = gpd.GeoDataFrame({
            'geoid20': ['123456789012'],
            'natwalkind': [11.25],
            'd4a_ranked': [14],
            'd2a_ranked': [11],
            'd3b_ranked': [9],
            'geometry': [Point(-83.9207, 35.9606).buffer(0.01)]
        }, crs='EPSG:4326')

        with patch('services.walkability.folium.Choropleth') as mock_choropleth:
            mock_layer = Mock()
            mock_layer.add_to.return_value = mock_layer
            mock_choropleth.return_value = mock_layer
            create_map(location, gdf, buffer_size=1.0)

            assert mock_choropleth.call_args.kwargs['fill_color'] == CHOROPLETH_COLORMAP
