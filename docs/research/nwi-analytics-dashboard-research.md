# National Walkability Index: Analytics & Dashboard Research

**Research Date:** 2026-02-19  
**Purpose:** Inform data analytics dashboard design for NWI project

---

## Executive Summary

The EPA's National Walkability Index (NWI) has been extensively researched and applied across urban planning, public health, and equity analysis. This research synthesis identifies key analytical approaches, visualization patterns, and research gaps to inform dashboard design.

**Key Finding:** While NWI data is widely available and validated, most existing dashboards focus on simple mapping and score display. There's opportunity for deeper analytics around health outcomes, equity analysis, spatial patterns, and comparative analysis.

---

## 1. Existing Dashboard Examples & Patterns

### Major Dashboard Platforms

#### **City Health Dashboard**
- **Scale:** 0-100 (using Walk Score data, not NWI)
- **Features:** City-level averages, neighborhood-level details
- **Approach:** Explains why walkability matters for health outcomes
- **Limitation:** Uses Walk Score, not NWI

#### **EPA's Walkability Index (ArcGIS)**
- **Scale:** 1-20 (NWI)
- **Features:** Interactive map visualization, census tract level
- **Visualization:** Quintiles for easier interpretation
- **Data:** Based on pedestrian-oriented intersections, occupied housing, job diversity, commute modes
- **URL:** https://experience.arcgis.com/experience/4e9b4ebfcf814fd19a73df1bd6c1ff4c/page/Walkability-Index

#### **CTstreets Walkability Map**
- **Features:** Multiple visualization layers (overall walkability, landscape, crime safety, traffic safety, proximity, infrastructure)
- **Interactivity:** Toggle layers, examine at street segment and population levels
- **Scale:** 5-15 minute walksheds
- **Notable:** Combines walkability with safety metrics

#### **National Walkability Index Interactive Maps (Virginia Equity Center)**
- **Features:** Customizable mapping tools, click-to-view scores and attributes
- **Ranking:** Block groups based on street intersection density, transit proximity, land use diversity
- **URL:** https://virginiaequitycenter.github.io/summer-sandbox/presentations/Walkability.html

### Common Dashboard Patterns

1. **Mapping-first approach:** Most dashboards lead with interactive maps
2. **Score display:** Show NWI scores (1-20) prominently
3. **Component breakdown:** Display individual dimensions (D2a, D2b, D3b, D4a)
4. **Quintile visualization:** Group scores into 5 categories for easier interpretation
5. **Population-weighted scoring:** Reflect where people actually live

---

## 2. Research Applications & Findings

### Health Outcomes Research

**Key Studies:**
- **2015 National Health Interview Survey Analysis** (CDC/PMC)
- **2020 National Health Interview Survey Analysis** (Wiley)

**Findings:**
- **Transportation walking:** Increases from 21.6% (least walkable) to 51.6% (most walkable) — **23 percentage point increase**
- **Leisure walking:** Increases from 48.4% to 56.5% across walkability spectrum
- **Physical activity:** Higher walkability correlates with increased physical activity
- **Obesity:** Reduced obesity rates in more walkable areas
- **Urban vs Rural:** Associations strongest in urban areas, minimal in rural areas

**Dashboard Opportunity:** Health outcomes correlation visualization (walkability vs. walking rates, obesity rates)

### Equity & Environmental Justice Research

**Key Studies:**
- **Nationwide analysis of socially vulnerable populations** (MDPI)
- **Comparative study:** Charlotte, NC; Pittsburgh, PA; Portland, OR (Taylor & Francis)
- **Environmental Justice in 15-Minute City** (MDPI)

**Findings:**
- **Racial disparities:** Communities of color live in less-walkable neighborhoods with fewer street lights, higher speed limits, more police stops
- **City variability:** Significant differences in equitable access across cities
  - Charlotte: Greatest inequity, most "walk-vulnerable" areas
  - Portland & Pittsburgh: More equitable, but unique spatial distributions
- **Social vulnerability:** High social vulnerability + low walkability = "walk-vulnerable" areas
- **Infrastructure gaps:** Less walkable areas have fewer amenities, worse infrastructure

**Dashboard Opportunity:** Equity analysis overlays (NWI vs. socioeconomic indicators, racial demographics, social vulnerability index)

### Spatial Pattern Analysis

**Key Patterns Identified:**
- **Rural areas:** Score ~1.2
- **Suburban residential:** Score ~8.3
- **Historic main streets/downtowns:** Score ~13.7
- **City centers/suburban town centers:** Score ~17.5+

**Research Applications:**
- GIS analysis of urban development patterns
- Spatial correlation with transportation behavior
- Regional comparisons (metropolitan areas, states)

**Dashboard Opportunity:** Spatial pattern analysis (heat maps, regional comparisons, urban-rural gradients)

---

## 3. Research Gaps & Opportunities

### What's Missing in Existing Dashboards

1. **Health outcomes integration:** Most dashboards show scores but don't visualize health correlations
2. **Equity analysis:** Limited integration of socioeconomic and demographic overlays
3. **Temporal analysis:** NWI is static; few dashboards show trends or changes over time
4. **Comparative analytics:** Limited side-by-side comparison tools (your Compare page addresses this!)
5. **Component analysis:** Most show composite scores but don't deeply analyze individual dimensions
6. **Contextual analysis:** Limited integration with complementary datasets (e.g., WAS, Walk Score, crime data)

### Unique Opportunities for Your Dashboard

Based on your existing project structure:

1. **Multi-location comparison:** Your `/compare` route is ahead of most existing dashboards
2. **Component dimension analysis:** Deep dive into D2a, D2b, D3b, D4a relationships
3. **"Nearby better" analytics:** Your delta-based search is unique
4. **Integration potential:** WAS (Walkable Accessibility Score) integration for "hollow neighborhood" detection
5. **Custom radius analysis:** Your buffer/search radius flexibility enables unique insights

---

## 4. Recommended Dashboard Features

### Core Analytics (High Priority)

1. **Health Outcomes Correlation**
   - NWI score vs. transportation walking rates
   - NWI score vs. leisure walking rates
   - NWI score vs. obesity rates (if data available)
   - Urban vs. rural breakdowns

2. **Equity Analysis**
   - NWI score vs. socioeconomic indicators
   - NWI score vs. racial demographics
   - Social vulnerability index overlay
   - "Walk-vulnerable" area identification

3. **Component Dimension Analysis**
   - D2a (Employment & Housing Mix) distribution
   - D2b (Employment Diversity) distribution
   - D3b (Intersection Density) distribution
   - D4a (Transit Proximity) distribution
   - Component correlation matrix
   - Which components drive high/low scores?

4. **Spatial Pattern Analysis**
   - Regional comparisons (metropolitan areas, states)
   - Urban-rural gradient visualization
   - Score distribution histograms
   - Geographic clustering analysis

### Advanced Analytics (Medium Priority)

5. **Comparative Analytics** (enhance existing `/compare`)
   - Multi-location comparison (3+ locations)
   - Component-by-component comparison
   - Score difference visualization
   - "Better" candidate analysis with multiple criteria

6. **Temporal Analysis** (if historical data available)
   - Score changes over time
   - Neighborhood momentum indicators
   - Stability vs. change patterns

7. **Integration Analytics**
   - NWI vs. WAS (Walkable Accessibility Score) correlation
   - "Hollow neighborhood" detection (high NWI, low WAS)
   - Multi-metric composite scores

### Visualization Patterns to Adopt

- **Quintile grouping:** Group scores into 5 categories for easier interpretation
- **Population-weighted metrics:** Reflect where people actually live
- **Layer toggles:** Allow users to show/hide different data layers
- **Interactive tooltips:** Click-to-view detailed scores and attributes
- **Comparative views:** Side-by-side or overlay comparisons

---

## 5. Data Sources & Integration Opportunities

### Complementary Datasets

1. **Walkable Accessibility Score (WAS)**
   - Pre-calculated: `US_WAS_1997_2019` shapefile
   - Temporal data: 1997-2019
   - Validated against Walk Score (ρ=0.912)
   - See: `docs/walkable_accessibility_score_paper_notes.md`

2. **Health Data**
   - National Health Interview Survey (NHIS) data
   - CDC health outcome data
   - Obesity rates by geography

3. **Equity Data**
   - Social Vulnerability Index (CDC)
   - Census demographic data
   - American Community Survey (ACS) data

4. **Transportation Data**
   - Transit stop locations
   - Commute mode data
   - Transportation infrastructure

### Integration Strategy

- **Spatial joins:** Join by GEOID (Census Block Group identifier)
- **API endpoints:** Consider adding analytics endpoints to your FastAPI backend
- **Caching:** Pre-compute common analytics queries
- **Incremental loading:** Load complementary datasets on-demand

---

## 6. Research Citations & References

### Key Papers

1. **Associations between the National Walkability Index and walking among US Adults — National Health Interview Survey, 2015**
   - CDC: https://stacks.cdc.gov/view/cdc/111032
   - PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC8544176/
   - Key finding: 21.6% → 51.6% transportation walking increase

2. **Higher Walkability Associated with Increased Physical Activity and Reduced Obesity among U.S. Adults**
   - PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9877111/
   - Wiley: https://onlinelibrary.wiley.com/doi/10.1002/oby.23634

3. **Do Socially Vulnerable Urban Populations Have Access to Walkable, Transit-Accessible Neighborhoods?**
   - MDPI: https://www.mdpi.com/2413-8851/7/1/6

4. **Equity in neighbourhood walkability? A comparative analysis of three large U.S. cities**
   - Taylor & Francis: https://www.tandfonline.com/doi/full/10.1080/13549839.2017.1297390

5. **Walkability Indices—The State of the Art and Future Directions: A Systematic Review**
   - MDPI: https://www.mdpi.com/2071-1050/16/16/6730

### Official Resources

- **EPA National Walkability Index User Guide:** https://www.epa.gov/smartgrowth/national-walkability-index-user-guide-and-methodology
- **EPA Methodology PDF:** https://www.epa.gov/sites/default/files/2021-06/documents/national_walkability_index_methodology_and_user_guide_june2021.pdf
- **Data.gov:** https://catalog.data.gov/dataset/walkability-index8
- **ArcGIS REST Service:** https://gispub.epa.gov/arcgis/rest/services/OA/WalkabilityIndex/MapServer

---

## 7. Recommendations for Dashboard Design

### Phase 1: Core Analytics (MVP)
- Health outcomes correlation charts
- Component dimension analysis
- Spatial pattern visualizations
- Enhanced comparison tools

### Phase 2: Equity & Integration
- Equity analysis overlays
- WAS integration for "hollow neighborhood" detection
- Multi-metric composite views

### Phase 3: Advanced Analytics
- Temporal analysis (if data available)
- Predictive analytics
- Custom query builder

### Design Principles
- **Research-backed:** Ground visualizations in validated research findings
- **Accessible:** Use quintiles and clear labels for general audiences
- **Interactive:** Enable exploration, not just display
- **Contextual:** Provide interpretation guidance and limitations
- **Comparative:** Leverage your unique multi-location comparison capability

---

## Next Steps

1. **Prioritize features** based on research findings and user needs
2. **Design mockups** for core analytics visualizations
3. **Plan data integration** for complementary datasets (WAS, health, equity)
4. **Create session** in `docs/sessions/active/` for dashboard development
5. **Reference this document** during dashboard design and development

---

*Research compiled from web searches, academic papers, and existing dashboard analysis. Last updated: 2026-02-19*
