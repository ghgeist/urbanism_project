# National Walkability Index

The National Walkability Index is a tool that measures the relative walkability of communities within the United States. The dataset covers every block group in the nation, providing a basis for comparing walkability from community to community.

## Data Availability

The National Walkability Index data are available at the block group level, a unit of census geography that is smaller than a census tract and larger than a census block. Every block group in the United States is assigned a National Walkability Index score.

## Methodology

The National Walkability Index is based on measures of the built environment that affect the probability of whether people walk as a mode of transportation:

- **Street intersection density**
- **Proximity to transit stops**
- **Diversity of land uses**

Although numerous factors influence walking, these measures were chosen for the National Walkability Index because they can be measured using variables in the Smart Location Database (SLD), which has nationwide data availability and consistency at the block group level. This limited set of variables also helps make the index simple and easy for a general audience to understand.

## Variables

The selected variables from the SLD are:

- **Intersection density** (SLD variable D3b): Higher intersection density is correlated with more walk trips.
- **Proximity to transit stops** (SLD variable D4a): Distance from population center to nearest transit stop in meters. Shorter distances correlate with more walk trips.
- **Diversity of land uses**:
  - **Employment mix** (SLD variable D2b_E8MixA): The mix of employment types in a block group (such as retail, office, or industrial). Higher values correlate with more walk trips.
  - **Employment and household mix** (SLD variable D2a_EpHHm): The mix of employment types and occupied housing. A block group with a diverse set of employment types (such as office, retail, and service) plus many occupied housing units will have a relatively high value. Higher values correlate with more walk trips.

## Scoring Methodology

To determine the walkability scores, these variables were used to rank every block group in the United States. Each block group was assigned four ranked scores, one for each of the variables above.

To score block groups, the block groups were placed into 20 quantiles by variable value (quantiles are groupings with equal numbers of records), each containing 5 percent of the total block groups. The block groups were then assigned a rank from 1 to 20 depending upon their quantile position:

- A ranked score of **1** was assigned to block groups with the lowest relative values influencing walking
- A ranked score of **20** was assigned to block groups with the highest relative values influencing walking
- Intermediate scores were assigned for values in between

## Query Requirements

Return a query that shows the following per geoid20:

- Intersection Density (D3b)
- Proximity to transit stops (D4a)
- Employment Mix (D2b_E8MixA)
- Employment and Household Mix (D2a_EpHHm)
- National Walkability Index Score
