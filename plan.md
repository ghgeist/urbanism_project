---
created: 2025-11
updated: 2026-01-21
---
# **Walkability Index: Execution Plan**

---

## **Quick Reference**

- **Status:** In Progress
- **Priority:** High
- **Estimated Time:** 0.5–1 day (reduced since no migration needed)
- **MVP Done (for portfolio):** Streamlit demo is reachable + returns results for 1–2 known test inputs; screenshots + architecture diagram exist; portfolio tile can ship even if UI is minimal.
- **Validation checkpoint (do early):** ✅ Complete - Hosted environment connects to PostGIS and runs queries successfully (203,645 rows loaded, PostGIS 3.5 enabled).
- **Stop condition:** If screenshots/diagram/portfolio integration takes longer than timebox, ship static artifacts (diagram + screenshots + explanation) and move on.

---

## **Execution Checklist**

### **A. Streamlit App & Database Setup**

- [x] Confirm current Streamlit version is fully committed and tagged in GitHub
- [x] Migrate from Neon PostgreSQL to Replit PostgreSQL (storage limits)
- [x] Update connection logic to support both Replit env vars and Streamlit secrets
- [x] Enable PostGIS 3.5 extension on Replit PostgreSQL
- [x] Load walkability data (203,645 rows successfully loaded)
- [x] Create spatial indexes for query optimization
- [x] Organize data folder structure (renamed files for clarity, removed intermediate files)
- [x] Add automatic CSV download capability from cloud storage
- [x] Test database connectivity and query performance

### **B. Deployment**

- [x] Streamlit app working in Replit
- [x] Environment variables configured for Replit PostgreSQL connection
- [ ] Test cold starts and basic load
- [ ] Capture final Replit URL for portfolio

### **C. Diagram + Screenshots**

- [ ] Create architecture diagram showing:
  - [ ] UI → Streamlit service → PostGIS → response → map rendering
- [ ] Write short bullet-list description of pipeline:
  - [ ] Ingest EPA National Walkability Index and relevant geospatial layers
  - [ ] Clean and normalize
  - [ ] Simplify geometries for web rendering
  - [ ] Load into PostGIS with spatial indexes
  - [ ] Query via Streamlit service for address/radius
- [ ] Capture key screenshots (desktop + mobile view if possible)

### **D. Portfolio Integration**

- [ ] Add Walkability tile to website homepage with:
  - [ ] Short problem statement
  - [ ] 1-2 sentence summary
  - [ ] "What this demonstrates" block
  - [ ] Architecture diagram
  - [ ] Key screenshots
  - [ ] Link to demo
  - [ ] Link to GitHub repo
- [ ] Add to Resume Featured Projects
- [ ] Add to LinkedIn Featured

### **E. Repo Publicization**

- [ ] Expose full project repo publicly (with secrets scrubbed):
  - [ ] Ingestion scripts
  - [ ] Geometry simplification logic
  - [ ] PostGIS schema and migration scripts
  - [ ] Streamlit app code
  - [ ] Deployment configuration
- [ ] Add or update top-level README that orients reviewers to:
  - [ ] `ingest/`
  - [ ] `db/`
  - [ ] `app/`
  - [ ] How to run locally, at a high level

### **F. Retro (Calibrate Other Plans)**

- [ ] Write a short retro after shipping the MVP:
  - [ ] What took longer than expected? Why?
  - [ ] What was surprisingly fast?
  - [ ] What broke in deployment or env management?
  - [ ] What “definition of done” was unclear at start?
  - [ ] What 2 process changes will you apply to the other 3 flagship plans?
- [ ] Update the other scope docs with calibrated timeboxes and stop conditions based on this retro

---

## **Context & Strategy (Reference)**

### **Role and Purpose**

Walkability is one of your four flagship projects and serves as the **primary domain anchor** for climate/housing/built-environment work. It demonstrates:

* real-world urban systems and land-use modeling  
* geospatial data-product design (EPA National Walkability Index)  
* turning complex public datasets into legible, usable tools  
* practical alignment with planners, residents, and housing-adjacent decision makers

It pairs with The Replacement Trap as the core of your domain story and complements Signal Storm (engineering depth) and Bantr (full-stack execution).

### **Portfolio Strategy**

#### **Primary Domain Tile**

Walkability appears as a top-row tile, alongside The Replacement Trap.

Primary narrative:  
**"Making national walkability data usable for real housing and planning decisions."**

Supporting themes:

* geospatial systems  
* public data legibility  
* climate/housing-adjacent decision support

### **Hosting and Stack Strategy**

#### **Target Stack**

* Backend: Streamlit service layer (Python)  
* Database: PostGIS (Replit PostgreSQL)  
* Frontend: Streamlit UI with Folium maps  
* Hosting: Replit with Streamlit (aligned with broader stack)

#### **Deployment Plan**

1. ✅ **Streamlit app is working in Replit**  
2. ✅ **Migrated to Replit PostgreSQL** (from Neon due to storage limits)  
3. ✅ **PostGIS 3.5 enabled** with spatial indexing  
4. ✅ **Database loaded** with 203,645 rows of walkability data  
5. ✅ **Connection logic updated** to support Replit env vars and Streamlit secrets  
6. ✅ **UI is stable** with address/radius queries and map visualization  
7. [ ] Finalize deployment configuration and capture URL

Rationale:

* Streamlit provides rapid development and good UX for geospatial data exploration.  
* Replit PostgreSQL offers more generous storage limits than Neon free tier.  
* Replit provides a stable, low-friction interactive demo.  
* No migration needed since Streamlit is working well.

### **Public-Facing Experience**

#### **A. Interactive Tool (Primary)**

The interactive app is the main artifact.

Target UX:

* simple start state (address + radius input)  
* clear map view with walkability overlay  
* basic hover/tooltip behavior for scores  
* short explanation of what the score represents

#### **B. Static Fallback (Secondary)**

On the portfolio page, include:

* 2–3 high-quality screenshots of the app  
* brief explanation of a typical usage scenario

This covers you if the app is temporarily unreachable.

### **Diagram and Data Pipeline**

#### **Architecture Diagram (Chosen)**

Create a concise diagram showing:

* UI → Streamlit service → PostGIS → response → map rendering

This serves as the **10-second systems view** for hiring managers.

#### **Soft Recommendation: Pipeline Description (Text)**

Instead of a full pipeline diagram, encode the data pipeline as a short bullet list on the portfolio page:

* ingest EPA National Walkability Index and relevant geospatial layers  
* clean and normalize  
* simplify geometries for web rendering  
* load into PostGIS with spatial indexes  
* query via Streamlit service for address/radius

This gives enough technical detail without an extra visual asset.

### **Repo Strategy**

#### **Full Repo Exposure**

You will expose the full project repo publicly (with secrets scrubbed):

* ingestion scripts  
* geometry simplification logic  
* PostGIS schema and migration scripts  
* Streamlit app code  
* deployment configuration

Rationale:

* "seeing is believing" for geospatial/data-product work  
* strong support for domain + systems credibility  
* aligns with the full-exposure approach chosen for Signal Storm

Add or update a top-level README that orients reviewers to:

* `ingest/`  
* `db/`  
* `app/`  
* how to run locally, at a high level

### **Public Narrative**

Primary framing:  
 **"An interactive geospatial data product that converts the EPA National Walkability Index into a usable tool for understanding neighborhood walkability and housing context."**

Supporting elements:

* you work with messy public data  
* you care about how real people make sense of urban systems  
* you design for clarity, not just maps

This links directly to your climate/housing positioning.

### **Portfolio Placement**

#### **Featured on:**

* Resume (Featured Projects)  
* LinkedIn (Featured section)  
* Website homepage (top row with The Replacement Trap)

Tile contents:

* short problem statement  
* 1–2 sentence summary  
* architecture diagram  
* key screenshots  
* link to interactive demo  
* link to GitHub repo

### **Out of Scope**

* No major expansion of functionality (keep the core query + visualization pattern).  
* No over-engineering of the frontend (keep UI simple and clear).  
* No full redesign of PostGIS schema.  
* No new data sources beyond what is already in scope.
