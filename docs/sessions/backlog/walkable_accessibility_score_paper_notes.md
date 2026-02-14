# Notes from the Walkable Accessibility Score (WAS) Paper

**Source:** Credit, K., Farah, I., Talen, E., Anselin, L., & Ghomrawi, H. (2025). The Walkable Accessibility Score (WAS): A spatially-granular open-source measure of walkability for the continental US from 1997-2019. *Environment and Planning B: Urban Analytics and City Science*.  
**DOI:** [10.1177/23998083251377116](https://doi.org/10.1177/23998083251377116)  
**Code & data:** [kcredit/Walkable-Accessibility-Score](https://github.com/kcredit/Walkable-Accessibility-Score)

---

## What the paper gives us

### 1. **Optimized WAS formula parameters**

From the paper’s optimized specification:

| Parameter | Value | Meaning |
|-----------|--------|--------|
| **decay** | 0.008 | Distance decay; score drops with distance |
| **upper** | 800 m | Max walking distance (meters) considered |
| **k** | 30 | Number of nearest amenities (opportunities) used |

- **Geography:** Block group scale; demand = block group centroids, supply = POIs (businesses, schools, parks).
- **Distance:** Euclidean distance in a projected CRS (e.g. Albers Equal Area, ESRI:102003); no network required.
- **Output:** Score 0–30; higher = more walkable accessibility.

Use these values if we implement or cite WAS in this repo.

### 2. **Validation**

- Optimized WAS vs Walk Score® (2011): **Spearman ρ = 0.912**.
- Useful for product/interpretation guardrails: we can describe WAS as “validated against Walk Score” when we add it.

### 3. **Amenity categories (from repo notebooks)**

POI types used in WAS (NAICS-based in the repo, plus external sources):

- **Retail / services:** Groceries (4451), pharmacies (4461), retail (4421, 4431, 4453, 4481–4483, 4523, 4531, 4532, 4539), banks (5221), bookstores (451211), bakeries (311811), entertainment (4511).
- **Food:** Restaurants (NAICS2 72).
- **Other:** Schools (Great Schools 2011), parks (e.g. ArcGIS 2021 centroids).

We don’t need to replicate NAICS filtering if we use their pre-calculated WAS; if we ever compute WAS ourselves, this list defines “amenities” in their sense.

### 4. **Concepts we can use in Slack Surface Explorer**

- **Built potential vs actualized convenience**  
  NWI = built environment (connectivity, land use mix, transit proximity). WAS = destination density (amenities within ~800 m).  
  → “Everyday convenience” can stay NWI-based; “Amenity richness” or “Destination density” can be WAS-based.

- **“Hollow neighborhood”**  
  High NWI (good bones) + low WAS (few destinations) → place has walkable structure but few nearby amenities.  
  → Strengthens **Walkable Island** logic: we can flag “high NWI, low WAS” as a distinct signal (e.g. “Walkable Island” vs “Destination sparse”).

- **Temporal (1997–2019)**  
  Pre-calculated WAS by year → “Stability trend” or “Neighborhood momentum” (e.g. 2010 vs 2019) without running WAS ourselves.

### 5. **Implementation notes (from paper + repo)**

- Euclidean distance in projected CRS; no routing. Can be run at scale on a laptop.
- Pre-calculated block-group WAS: **US_WAS_1997_2019** shapefile in repo [output folder](https://github.com/kcredit/Walkable-Accessibility-Score/tree/main/output).
- Replication of their exact scores requires InfoUSA business data; we can still use their **aggregated WAS** and their **parameters** (decay, upper, k) for any future local calculation or documentation.

---

## Summary: what to pull into this repo

| Use case | What to pull from the paper |
|----------|-----------------------------|
| **Add WAS as a metric** | Use pre-calculated US_WAS_1997_2019; join to block groups by GEOID. |
| **Define “Amenity richness”** | Label as WAS (0–30), cite decay=0.008, upper=800 m, k=30. |
| **Refine Walkable Island** | Optionally add “high NWI + low WAS” = hollow / destination-sparse. |
| **Upgrade Potential** | Backlog idea: require both NWI and WAS improvement deltas for “better”. |
| **Stability / momentum** | Use WAS 2010 vs 2019 (or other years) from same shapefile. |
| **Guardrails** | Describe WAS as “destination-based accessibility (0–30), validated against Walk Score (ρ=0.91)”. |

---

*Doc created from paper abstract, Illinois Experts page, and GitHub README/notebooks; SAGE full text was not accessed.*
