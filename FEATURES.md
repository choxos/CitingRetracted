# 📊 Post-Retraction Citation Tracker (PRCT) - Enhanced Analytics

The Post-Retraction Citation Tracker (PRCT) database now includes comprehensive analytics specifically focused on post-retraction citations - one of the most critical issues in academic integrity.

## 🚨 Post-Retraction Citation Tracking

### What are Post-Retraction Citations?
Post-retraction citations occur when researchers cite a paper **after** it has been officially retracted. This is particularly concerning because:

- Authors should be aware the paper has been retracted
- It perpetuates potentially flawed or fraudulent research
- It undermines the retraction process
- It can mislead other researchers

### 📊 Enhanced Analytics Dashboard

#### 1. **Homepage Statistics**
- **Post-Retraction Citation Count**: Prominent display of total citations after retraction
- **Visual Indicators**: Clear red warning indicators for problematic citations
- **Percentage Breakdown**: Shows what percentage of all citations are post-retraction

#### 2. **Paper Detail Pages**
- **Citation Timeline Analysis**: Shows exactly when citations occurred relative to retraction date
- **Post-Retraction Breakdown**:
  - Within 30 days of retraction
  - Within 1 year of retraction  
  - Within 2 years of retraction
  - After 2+ years (most concerning)
- **Latest Citation Tracker**: Shows how recently the retracted paper was cited
- **Warning Alerts**: Prominent warnings when post-retraction citations exist

#### 3. **Analytics Dashboard**
- **Post-Retraction Timeline Chart**: Visual breakdown of when post-retraction citations occur
- **Most Problematic Papers**: Ranking of papers with highest post-retraction citation counts
- **Journal Analysis**: Which journals have the most post-retraction citation issues
- **Subject Area Analysis**: Which research fields have the biggest problems

### 🔍 Search & Discovery

#### Enhanced Search Results
- **Post-Retraction Citation Counts**: Displayed for each paper in search results
- **Visual Indicators**: Red badges highlighting papers with post-retraction citations
- **Filtering Options**: Filter by papers with/without post-retraction citations

#### Autocomplete Suggestions
- Shows post-retraction citation counts in search suggestions
- Helps researchers quickly identify problematic papers

### 📈 Interactive Visualizations

#### 1. **Citation Timeline Charts**
- **Bar Charts**: Show citation patterns before/during/after retraction
- **Timeline Views**: Visual timeline of when citations occurred
- **Color Coding**: 
  - Green: Pre-retraction (acceptable)
  - Yellow: Same day as retraction
  - Red: Post-retraction (concerning)

#### 2. **Post-Retraction Analysis Charts**
- **Timeline Distribution**: How long after retraction citations continue
- **Journal Comparison**: Which journals have the most issues
- **Trend Analysis**: Are post-retraction citations increasing over time?

### 🎯 Specific Metrics Tracked

#### Paper-Level Analytics
- **Total Citations**: All citations for the paper
- **Post-Retraction Count**: Citations after retraction date
- **Post-Retraction Percentage**: What % of citations are post-retraction
- **Days Since Latest Citation**: How recently it was cited
- **Average Days After Retraction**: Typical delay between retraction and citation

#### Timeline Buckets
- **Within 30 days**: Might indicate lag in retraction notice propagation
- **Within 6 months**: Concerning but possibly explainable
- **Within 1 year**: Definitely problematic
- **Within 2 years**: Very concerning
- **After 2+ years**: Extremely problematic - no excuse for citing

#### Database-Wide Analytics
- **Total Post-Retraction Citations**: Across entire database
- **Percentage of All Citations**: What % of database citations are post-retraction
- **Most Cited Retracted Papers**: Papers still being heavily cited
- **Worst Offending Journals**: Publications with most post-retraction citations
- **Subject Area Problems**: Research fields with biggest issues

### 🚨 Warning Systems

#### Visual Indicators
- **Red Badges**: Post-retraction citation counts prominently displayed
- **Warning Alerts**: Clear alerts when viewing papers with post-retraction citations
- **Timeline Highlighting**: Color-coded citation timelines
- **Dashboard Warnings**: Analytics dashboard highlights concerning trends

#### Data Export
- **Enhanced Export**: CSV/JSON exports include post-retraction analytics
- **Researcher Tools**: Data formatted for academic research use
- **Citation Analysis**: Pre-built analytics for research papers

### 🔧 Technical Implementation

#### Database Design
- **Automated Calculation**: `days_after_retraction` automatically calculated
- **Indexed Queries**: Fast filtering and sorting by post-retraction status
- **Timeline Analysis**: Efficient querying of citation patterns

#### API Endpoints
- **Real-time Data**: AJAX endpoints for interactive charts
- **Filtering**: API supports filtering by post-retraction status
- **Analytics Data**: Dedicated endpoints for dashboard visualizations

#### Performance Optimizations
- **Cached Calculations**: Pre-calculated post-retraction counts
- **Efficient Queries**: Optimized database queries for large datasets
- **Background Processing**: Citation fetching happens in background

### 📊 Use Cases

#### For Researchers
- **Literature Review**: Identify if papers in your field are citing retracted work
- **Reference Checking**: Verify papers you're citing haven't been retracted
- **Research Integrity**: Understand citation patterns in your discipline

#### For Journal Editors
- **Quality Control**: Identify papers citing retracted work
- **Editorial Decisions**: Factor in post-retraction citation patterns
- **Author Guidelines**: Educate authors about proper citation practices

#### For Institutions
- **Research Oversight**: Monitor institutional research for citation integrity
- **Training Materials**: Use data to educate researchers
- **Policy Development**: Evidence-based retraction policies

#### For Meta-Research
- **Citation Analysis**: Study patterns in post-retraction citations
- **Field Comparisons**: Compare disciplines for citation integrity
- **Temporal Trends**: Track changes in citation behavior over time

### 🎯 Key Insights Revealed

The enhanced analytics can reveal:

1. **Citation Persistence**: How long retracted papers continue to be cited
2. **Field Differences**: Which research areas have better/worse citation practices
3. **Journal Effectiveness**: How well retraction notices reach the community
4. **Geographic Patterns**: Whether certain regions have different citation behaviors
5. **Temporal Trends**: Whether post-retraction citations are increasing/decreasing

### 🚀 Future Enhancements

Planned improvements include:
- **Machine Learning**: Predict likelihood of post-retraction citations
- **Alert Systems**: Notify when retracted papers are being cited
- **Integration**: Connect with reference managers and writing tools
- **Real-time Monitoring**: Live tracking of new citations to retracted papers

---

**This comprehensive post-retraction citation analysis makes the database a unique tool for research integrity and academic quality control.** 🎯 