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
        <h2>Data source</h2>
        <p>
          All scores come from the <strong>EPA National Walkability Index (NWI)</strong>.
          The NWI assigns every U.S. census block group a value from 1 to 20 based on
          four components: land-use mix, employment mix, street connectivity, and transit access.
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
            <strong>D2A (destinations)</strong> — Proximity to common destinations (e.g. retail, services).
          </li>
          <li>
            <strong>D2B (employment)</strong> — Employment density and mix.
          </li>
          <li>
            <strong>D3B (connectivity)</strong> — Street network connectivity (intersection density, block size).
          </li>
          <li>
            <strong>D4A (transit)</strong> — Transit stop availability and frequency.
          </li>
        </ul>
      </section>
    </div>
  );
}
