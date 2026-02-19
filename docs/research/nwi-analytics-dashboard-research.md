# National Walkability Index: Analytics and Dashboard Research

**Research Date:** February 19, 2026  
**Purpose:** To inform data analytics dashboard design for National Walkability Index applications

---

## Executive Summary

The Environmental Protection Agency's National Walkability Index (NWI) has been extensively researched and applied across urban planning, public health, and equity analysis domains. This research synthesis identifies key analytical approaches, visualization patterns, and research gaps to inform dashboard design decisions.

**Key Finding:** While NWI data is widely available and validated, most existing dashboards focus primarily on simple mapping and score display. Significant opportunities exist for deeper analytical capabilities including health outcomes correlation, equity analysis, spatial pattern identification, and comparative analysis.

---

## 1. Existing Dashboard Examples and Patterns

### Major Dashboard Platforms

#### **City Health Dashboard**
- **Scale:** 0-100 (utilizes Walk Score data, not NWI)
- **Features:** City-level averages, neighborhood-level detail views
- **Approach:** Emphasizes walkability's relationship to health outcomes
- **Limitation:** Utilizes Walk Score methodology rather than NWI

#### **EPA's Walkability Index (ArcGIS)**
- **Scale:** 1-20 (NWI standard)
- **Features:** Interactive map visualization at census tract level
- **Visualization:** Quintile-based categorization for interpretability
- **Data Foundation:** Pedestrian-oriented intersections, occupied housing density, job diversity, commute mode share
- **Reference:** https://experience.arcgis.com/experience/4e9b4ebfcf814fd19a73df1bd6c1ff4c/page/Walkability-Index

#### **CTstreets Walkability Map**
- **Features:** Multi-layer visualization system (overall walkability, landscape, crime safety, traffic safety, proximity, infrastructure)
- **Interactivity:** Layer toggling, examination at street segment and population levels
- **Scale:** 5-15 minute walksheds
- **Notable:** Integrates walkability metrics with safety indicators

#### **National Walkability Index Interactive Maps (Virginia Equity Center)**
- **Features:** Customizable mapping tools, click-to-view score and attribute details
- **Ranking Methodology:** Block groups ranked by street intersection density, transit proximity, land use diversity
- **Reference:** https://virginiaequitycenter.github.io/summer-sandbox/presentations/Walkability.html

### Common Dashboard Patterns

1. **Mapping-first approach:** Most dashboards employ interactive maps as the primary interface
2. **Score display:** NWI scores (1-20 scale) displayed prominently
3. **Component breakdown:** Individual dimension visualization (D2a, D2b, D3b, D4a)
4. **Quintile visualization:** Score grouping into five categories for enhanced interpretability
5. **Population-weighted scoring:** Metrics weighted to reflect actual population distribution

---

## 2. Research Applications and Findings

### Health Outcomes Research

**Key Studies:**
- **2015 National Health Interview Survey Analysis** (Centers for Disease Control and Prevention/PubMed Central)
- **2020 National Health Interview Survey Analysis** (Wiley Online Library)

**Findings:**
- **Transportation walking:** Prevalence increases from 21.6% (least walkable areas) to 51.6% (most walkable areas), representing a 23 percentage point increase
- **Leisure walking:** Prevalence increases from 48.4% to 56.5% across the walkability spectrum
- **Physical activity:** Higher walkability indices correlate positively with increased physical activity levels
- **Obesity:** Reduced obesity rates observed in more walkable areas
- **Urban vs. Rural:** Associations are strongest in urban areas, with minimal correlation observed in rural settings

**Dashboard Opportunity:** Health outcomes correlation visualization capabilities (walkability index versus walking rates, obesity rates)

### Equity and Environmental Justice Research

**Key Studies:**
- **Nationwide analysis of socially vulnerable populations** (Multidisciplinary Digital Publishing Institute)
- **Comparative study:** Charlotte, North Carolina; Pittsburgh, Pennsylvania; Portland, Oregon (Taylor & Francis)
- **Environmental Justice in 15-Minute City** (Multidisciplinary Digital Publishing Institute)

**Findings:**
- **Racial disparities:** Communities of color disproportionately reside in less-walkable neighborhoods characterized by fewer street lights, higher speed limits, and increased police stops
- **City variability:** Significant differences in equitable access observed across metropolitan areas
  - Charlotte: Exhibits greatest inequity, with highest concentration of "walk-vulnerable" areas
  - Portland and Pittsburgh: Demonstrate more equitable distributions, though with distinct spatial patterns
- **Social vulnerability:** Areas with high social vulnerability indices combined with low walkability scores constitute "walk-vulnerable" neighborhoods
- **Infrastructure gaps:** Less walkable areas demonstrate fewer amenities and inferior infrastructure quality

**Dashboard Opportunity:** Equity analysis overlay capabilities (NWI versus socioeconomic indicators, racial demographics, social vulnerability index)

### Spatial Pattern Analysis

**Key Patterns Identified:**
- **Rural areas:** Average score approximately 1.2
- **Suburban residential:** Average score approximately 8.3
- **Historic main streets and downtowns:** Average score approximately 13.7
- **City centers and suburban town centers:** Average score 17.5 and above

**Research Applications:**
- Geographic Information Systems analysis of urban development patterns
- Spatial correlation analysis with transportation behavior
- Regional comparative analysis (metropolitan areas, state-level comparisons)

**Dashboard Opportunity:** Spatial pattern analysis capabilities (heat maps, regional comparisons, urban-rural gradient visualizations)

---

## 3. Research Gaps and Opportunities

### Limitations in Existing Dashboards

1. **Health outcomes integration:** Most dashboards display scores but lack health correlation visualizations
2. **Equity analysis:** Limited integration of socioeconomic and demographic overlay capabilities
3. **Temporal analysis:** NWI data is static; few dashboards demonstrate temporal trends or change analysis
4. **Comparative analytics:** Limited side-by-side comparison functionality
5. **Component analysis:** Most dashboards display composite scores but lack deep analysis of individual dimensions
6. **Contextual analysis:** Limited integration with complementary datasets (e.g., Walkable Accessibility Score, Walk Score, crime data)

### Identified Opportunities for Enhanced Dashboard Capabilities

Based on current project architecture:

1. **Multi-location comparison:** Comparative analysis functionality exceeds capabilities of most existing dashboards
2. **Component dimension analysis:** In-depth examination of D2a, D2b, D3b, D4a dimension relationships
3. **Delta-based search analytics:** Unique capability for identifying areas with improved walkability metrics
4. **Integration potential:** Walkable Accessibility Score (WAS) integration for "hollow neighborhood" detection
5. **Custom radius analysis:** Flexible buffer and search radius parameters enable unique analytical insights

---

## 4. Recommended Dashboard Features

### Core Analytics (High Priority)

1. **Health Outcomes Correlation**
   - NWI score versus transportation walking rates
   - NWI score versus leisure walking rates
   - NWI score versus obesity rates (subject to data availability)
   - Urban versus rural breakdowns

2. **Equity Analysis**
   - NWI score versus socioeconomic indicators
   - NWI score versus racial demographics
   - Social vulnerability index overlay
   - "Walk-vulnerable" area identification

3. **Component Dimension Analysis**
   - D2a (Employment and Housing Mix) distribution
   - D2b (Employment Diversity) distribution
   - D3b (Intersection Density) distribution
   - D4a (Transit Proximity) distribution
   - Component correlation matrix
   - Identification of components driving high/low scores

4. **Spatial Pattern Analysis**
   - Regional comparisons (metropolitan areas, state-level)
   - Urban-rural gradient visualization
   - Score distribution histograms
   - Geographic clustering analysis

### Advanced Analytics (Medium Priority)

5. **Comparative Analytics** (enhancement of existing comparison functionality)
   - Multi-location comparison (three or more locations)
   - Component-by-component comparison
   - Score difference visualization
   - Multi-criteria candidate analysis

6. **Temporal Analysis** (subject to historical data availability)
   - Score changes over time
   - Neighborhood momentum indicators
   - Stability versus change pattern identification

7. **Integration Analytics**
   - NWI versus Walkable Accessibility Score (WAS) correlation
   - "Hollow neighborhood" detection (high NWI, low WAS)
   - Multi-metric composite score generation

### Visualization Patterns to Adopt

- **Quintile grouping:** Score categorization into five groups for enhanced interpretability
- **Population-weighted metrics:** Metrics weighted to reflect actual population distribution
- **Layer toggles:** User-controlled display of different data layers
- **Interactive tooltips:** Click-to-view detailed scores and attributes
- **Comparative views:** Side-by-side or overlay comparison capabilities

---

## 5. Data Sources and Integration Opportunities

### Complementary Datasets

1. **Walkable Accessibility Score (WAS)**
   - Pre-calculated dataset: `US_WAS_1997_2019` shapefile
   - Temporal coverage: 1997-2019
   - Validation: Correlation coefficient of 0.912 against Walk Score
   - Reference documentation: `docs/walkable_accessibility_score_paper_notes.md`

2. **Health Data**
   - National Health Interview Survey (NHIS) data
   - Centers for Disease Control and Prevention health outcome data
   - Obesity rates by geographic area

3. **Equity Data**
   - Social Vulnerability Index (Centers for Disease Control and Prevention)
   - Census demographic data
   - American Community Survey (ACS) data

4. **Transportation Data**
   - Transit stop location data
   - Commute mode share data
   - Transportation infrastructure datasets

### Integration Strategy

- **Spatial joins:** Join operations using GEOID (Census Block Group identifier)
- **API endpoints:** Consider implementing analytics endpoints within the FastAPI backend
- **Caching:** Pre-computation of common analytics queries
- **Incremental loading:** On-demand loading of complementary datasets

---

## 6. Research Citations and References

### Key Papers

1. **Associations between the National Walkability Index and walking among US Adults — National Health Interview Survey, 2015**
   - Centers for Disease Control and Prevention: https://stacks.cdc.gov/view/cdc/111032
   - PubMed Central: https://pmc.ncbi.nlm.nih.gov/articles/PMC8544176/
   - Key finding: Transportation walking prevalence increases from 21.6% to 51.6%

2. **Higher Walkability Associated with Increased Physical Activity and Reduced Obesity among U.S. Adults**
   - PubMed Central: https://pmc.ncbi.nlm.nih.gov/articles/PMC9877111/
   - Wiley Online Library: https://onlinelibrary.wiley.com/doi/10.1002/oby.23634

3. **Do Socially Vulnerable Urban Populations Have Access to Walkable, Transit-Accessible Neighborhoods?**
   - Multidisciplinary Digital Publishing Institute: https://www.mdpi.com/2413-8851/7/1/6

4. **Equity in neighbourhood walkability? A comparative analysis of three large U.S. cities**
   - Taylor & Francis: https://www.tandfonline.com/doi/full/10.1080/13549839.2017.1297390

5. **Walkability Indices—The State of the Art and Future Directions: A Systematic Review**
   - Multidisciplinary Digital Publishing Institute: https://www.mdpi.com/2071-1050/16/16/6730

### Official Resources

- **Environmental Protection Agency National Walkability Index User Guide:** https://www.epa.gov/smartgrowth/national-walkability-index-user-guide-and-methodology
- **Environmental Protection Agency Methodology PDF:** https://www.epa.gov/sites/default/files/2021-06/documents/national_walkability_index_methodology_and_user_guide_june2021.pdf
- **Data.gov:** https://catalog.data.gov/dataset/walkability-index8
- **ArcGIS REST Service:** https://gispub.epa.gov/arcgis/rest/services/OA/WalkabilityIndex/MapServer

---

## 7. Recommendations for Dashboard Design

### Phase 1: Core Analytics (Minimum Viable Product)
- Health outcomes correlation visualizations
- Component dimension analysis
- Spatial pattern visualizations
- Enhanced comparison tools

### Phase 2: Equity and Integration
- Equity analysis overlay capabilities
- Walkable Accessibility Score integration for "hollow neighborhood" detection
- Multi-metric composite views

### Phase 3: Advanced Analytics
- Temporal analysis (subject to data availability)
- Predictive analytics capabilities
- Custom query builder functionality

### Design Principles
- **Research-backed:** Visualizations grounded in validated research findings
- **Accessible:** Utilization of quintiles and clear labeling for general audiences
- **Interactive:** Enable exploratory analysis rather than static display
- **Contextual:** Provide interpretation guidance and methodological limitations
- **Comparative:** Leverage multi-location comparison capabilities

---

## Next Steps

1. **Prioritize features** based on research findings and user requirements
2. **Design mockups** for core analytics visualizations
3. **Plan data integration** for complementary datasets (Walkable Accessibility Score, health, equity)
4. **Create development session** in `docs/sessions/active/` for dashboard implementation
5. **Reference this document** during dashboard design and development phases

---

*Research compiled from web searches, academic papers, and existing dashboard analysis. Last updated: February 19, 2026*
