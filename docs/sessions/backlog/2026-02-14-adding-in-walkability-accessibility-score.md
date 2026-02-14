---
created: 2026-02-14
sources:
- https://journals.sagepub.com/doi/10.1177/23998083251377116
- https://experience.arcgis.com/experience/ce83fc13e21c415ab9e12427da3d53df?draft=true
- https://github.com/kcredit/Walkable-Accessibility-Score?tab=readme-ov-file
paper_notes: docs/walkable_accessibility_score_paper_notes.md
---

The **Walkable Accessibility Score (WAS)** project provides a critical missing layer to your current "Slack Surface Explorer" model: **Destination Density**. While the EPA National Walkability Index (NWI) focuses on the "bones" of a neighborhood—like street connectivity and land-use mix—the WAS measures the actual presence of **30** urban amenities (grocery stores, cafes, pharmacies, schools, parks, etc.) within the paper’s **optimized distance cap of 800 m** (decay=0.008, k=30). See `docs/walkable_accessibility_score_paper_notes.md` for parameters and citation.

Integrating this data allows you to move from measuring "Built Potential" (NWI) to "Actualized Convenience" (WAS).

### **Leveraging WAS for the Slack Profile**

* **The "Hollow Neighborhood" Signal:** By cross-referencing high NWI connectivity with low WAS accessibility, you can identify areas that have "walkable bones" but no actual destinations. This adds significant depth to your **Walkable Island Check**.
* **Temporal Flexibility (1997–2019):** The WAS dataset includes historical data. You can use this to calculate "Neighborhood Momentum"—whether an area’s flexibility is expanding or stagnating over decades.
* **Refined "Everyday Convenience":** You can blend the WAS 0–30 scale with the NWI 1–20 scale to create a more robust proxy for the "Coordination Burden" you're trying to solve.

---

### **Backlog Additions: WAS Integration**

#### **Data Engineering & Analysis**

* **Task 1: Spatial Join of WAS Dataset**
* **Action:** Download the `US_WAS_1997_2019` shapefile and ingest it into your Neon PostGIS database.
* **Implementation:** Perform a `LEFT JOIN` on the GEOID (Census Block Group) between your existing `national_walkability_index` and the new WAS table.


* **Task 2: Normalize Amenity Scores**
* **Action:** Re-scale the 0–30 WAS to a 0–1 decimal to align with your internal modeling metrics.



#### **Product Features**

* **Task 3: Implement the "Amenity Richness" Metric**
* **Action:** Add a new summary card to the **Profile Summary** section: "Amenity Richness".
* **Logic:** Use the WAS score to provide a neutral descriptor (e.g., "Full Amenity Access" vs. "Destination Sparse").


* **Task 4: Historical Slack Analysis**
* **Action:** Create a "Stability Trend" signal.
* **Logic:** Compare 2010 vs. 2019 WAS scores to tell the user if the "Everyday Convenience" of an area is historically stable or in flux.



#### **Interpretation & Guardrails**

* **Task 5: Update "Upgrade Potential" Logic**
* **Action:** Refine the "better" candidate criteria.
* **Logic:** A candidate location is only "Better" if both the NWI (built environment) *and* the WAS (amenity density) show a material improvement delta.
