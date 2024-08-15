--connection needs to be neon_urbanism -> neondb -> public
-- There should be 203645 rows in the database
SELECT (count(*) = 203645) AS is_expected_count
FROM national_walkability_index;


-- Working query!!!
-- The EPSG 4326 spatial reference system uses degrees of latitude and longitude as its units. 
-- This means that distances are measured in degrees, not in meters or feet.
with load_data as (
    select 
        geoid20,
        natwalkind, 
        geometry,
        st_setsrid(st_makepoint(-83.921026099999999, 35.9603948), 4326) as centroid -- Knoxville, TN coordinates, long/lat
    from national_walkability_index
)

-- Use the subquery to calculate the distance and count
select
    count(geoid20) as count
from load_data
where st_dwithin(centroid, geometry, 0.0145) is true;  -- this is distance in degrees