/**
 * Method / About: data source, disclaimer, and short explanation of metrics.
 */

export function Method() {
  return (
    <div className="method-page">
      <header className="method-page__header">
        <h1>Method</h1>
        <p className="method-page__tagline">
          How this tool works and what the numbers mean.
        </p>
      </header>

      <section className="method-page__section">
        <h2>Data sources</h2>
        <h3>EPA National Walkability Index (NWI)</h3>
        <p>
          The primary scores come from the <strong>EPA National Walkability Index (NWI)</strong>.
          The NWI assigns every U.S. census block group a value from 1 to 20 (higher = more walkable)
          based on four components: land-use mix, employment mix, street connectivity, and transit access.
          Data reflects conditions as of the 2020 Census and covers the 50 states, District of Columbia, and Puerto Rico.
          More information:{" "}
          <a
            href="https://www.epa.gov/smartgrowth/national-walkability-index-user-guide-and-methodology"
            target="_blank"
            rel="noopener noreferrer"
          >
            EPA National Walkability Index — User Guide and Methodology
          </a>
        </p>

        <h3>Walkable Accessibility Score (WAS)</h3>
        <p>
          A second, complementary measure: the <strong>Walkable Accessibility Score (WAS)</strong> from
          Credit et al. (2025). WAS scores every U.S. block group from 0 to 30 based on the number of nearby
          destinations — grocery and drug stores, shops, banks, bookstores, schools, parks, and food services — within
          roughly 1,600 m walking distance, weighted by a logistic distance decay. A score of 0 means there
          are no qualifying destinations within that range; scores near 30 indicate a dense cluster of nearby
          amenities. This app uses the <strong>2019 snapshot</strong> (the most recent year in the published
          dataset), and the coverage is 2010-Census block groups across the 48 contiguous states.
        </p>
        <p>
          Where NWI measures the <em>form</em> of the built environment (street design, density, mix), WAS
          measures <em>how much there is to walk to</em>. They are intentionally independent signals: the
          paper's authors tested combining them and found it did not improve the fit with commercial Walk
          Score&reg;, so this app surfaces them separately (for example, in the Hollow Neighborhood signal).
        </p>
        <p>
          Please cite the paper when referencing this data:{" "}
          <a
            href="https://doi.org/10.1177/23998083251377116"
            target="_blank"
            rel="noopener noreferrer"
          >
            Credit, K., Farah, I., Talen, E., Anselin, L., &amp; Ghomrawi, H. (2025). The Walkable
            Accessibility Score (WAS): A spatially-granular open-source measure of walkability for the
            continental US from 1997-2019. <em>Environment and Planning B</em>.
          </a>
          {" · "}
          <a
            href="https://github.com/kcredit/Walkable-Accessibility-Score"
            target="_blank"
            rel="noopener noreferrer"
          >
            Source code and data on GitHub
          </a>
        </p>
      </section>

      <section className="method-page__section">
        <h2>Descriptive, not causal</h2>
        <p>
          The index is a <strong>descriptive</strong> measure of existing conditions.
          It does not imply causation (e.g., that a higher score causes better health outcomes).
          Use it to compare places and inform discussion, not to assert cause and effect.
        </p>
      </section>

      <section className="method-page__section">
        <h2>What the metrics mean</h2>
        <ul>
          <li>
            <strong>National Walkability Index (NWI)</strong> — Composite score 1–20 combining
            the four components; higher means more walkable.
          </li>
          <li>
            <strong>D2A: Employment and Household Mix</strong> — The mix of employment types and occupied housing. 
            A block group with diverse employment types (office, retail, service) plus many occupied housing units will have a higher score.
          </li>
          <li>
            <strong>D2B: Employment Mix</strong> — The mix of employment types in a block group (retail, office, industrial). 
            Higher values indicate greater diversity of employment types.
          </li>
          <li>
            <strong>D3B: Street Intersection Density</strong> — The density of street intersections. 
            Higher intersection density is correlated with more walk trips and better street connectivity.
          </li>
          <li>
            <strong>D4A: Proximity to Transit Stops</strong> — Distance from population center to nearest transit stop. 
            Shorter distances (higher scores) correlate with more walk trips.
          </li>
          <li>
            <strong>Amenity Richness (WAS 2019)</strong> — Mean Walkable Accessibility Score on the
            0–30 scale over the selected radius; higher means more reachable destinations within a
            comfortable walk. The card shows "Unavailable" when the area is outside WAS coverage (for
            example, block groups whose GEOID changed between the 2010 and 2020 Censuses).
          </li>
          <li>
            <strong>Hollow Neighborhood</strong> — A combined signal that flags areas with walkable
            street design (high mean NWI) but few nearby destinations (low mean WAS). Good bones,
            missing amenities — a candidate for infill retail or services rather than street
            redesign.
          </li>
        </ul>
      </section>

      <section className="method-page__section">
        <h2>Technical constraints</h2>
        <p>
          This tool queries block groups within a 0.1–3.0 mile radius of the selected location.
          Geocoding accuracy depends on Nominatim results; some addresses may resolve to approximate locations.
          Upgrade Potential candidates must meet a minimum NWI improvement threshold (default: 2.0 points) to be shown.
        </p>
      </section>
    </div>
  );
}
