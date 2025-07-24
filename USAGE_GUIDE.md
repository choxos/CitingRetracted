# 🚀 Post-Retraction Citation Tracker (PRCT) - Usage Guide

## Overview

This guide covers how to use the fully enhanced Post-Retraction Citation Tracker (PRCT) database with comprehensive Retraction Watch integration and advanced stratified analytics.

## 🗃️ **New Database Features**

### **Enhanced Data Fields**
The database now includes all Retraction Watch fields:
- **Geographic Data**: Country, Institution tracking
- **Publisher Analytics**: Publisher-specific insights
- **Article Classification**: Article types and enhanced subjects
- **Access Status**: Open Access vs Paywalled analysis
- **PubMed Integration**: Direct links to PubMed entries
- **Comprehensive Links**: DOI, retraction notices, external URLs

## 📥 **Data Import System**

### **Import Retraction Watch CSV**
```bash
# Basic import
python manage.py import_retraction_watch sample_retraction_watch.csv

# Import with existing record updates
python manage.py import_retraction_watch data.csv --update-existing

# Preview import without saving (dry run)
python manage.py import_retraction_watch data.csv --dry-run

# Limit number of records (for testing)
python manage.py import_retraction_watch data.csv --limit 100
```

### **CSV Format Support**
The system now handles the complete Retraction Watch CSV format:
- **Date Format**: Supports "M/D/YYYY 0:00" format
- **Multiple Values**: Handles semicolon-separated countries, subjects, authors
- **Subject Cleaning**: Automatically removes technical prefixes like "(PHY)", "(B/T)"
- **Boolean Fields**: Smart parsing of "Yes/No" for paywalled status
- **Field Cleaning**: Automatic text cleaning and normalization

### **Test with Sample Data**
A sample CSV file is included (`sample_retraction_watch.csv`) with realistic test data:
```bash
python manage.py import_retraction_watch sample_retraction_watch.csv --dry-run
```

## 📊 **Enhanced Analytics Dashboard**

### **Access the Dashboard**
Visit: `http://localhost:8000/analytics/`

### **New Analytics Sections**

#### **1. Overview Tab**
- **Enhanced Statistics Cards**: With hover effects and progress indicators
- **Real-time Metrics**: Total papers, citations, post-retraction percentages
- **Quick Charts**: Citation patterns and timeline analysis

#### **2. Trends Tab**
- **Time-based Filtering**: 1 year, 3 years, 5 years, all time
- **Retraction Timeline**: Multi-year trend analysis
- **Comparative Analysis**: Before vs after retraction patterns
- **Subject Distribution**: Research area breakdown

#### **3. Patterns Tab** (New!)
- **Geographic Analysis**: Country-based retraction patterns
- **Publisher Impact**: Top problematic publishers
- **Article Type Distribution**: Research vs Review articles analysis
- **Open Access Analytics**: Access status impact on citations
- **Citation Heatmap**: Monthly patterns vs time after retraction
- **Journal Bubble Chart**: Multi-dimensional journal analysis

#### **4. Network Tab**
- **Interactive Network**: D3.js force-directed graphs
- **Draggable Nodes**: Explore journal and subject relationships
- **Dynamic Tooltips**: Detailed information on hover

### **Key New Visualizations**

#### **Geographic Distribution Chart**
- **Dual-axis Design**: Retractions count + Open Access rate
- **Country Rankings**: Top 15 countries by retraction count
- **Interactive Tooltips**: Detailed metrics per country

#### **Publisher Analysis Chart**
- **Horizontal Bar Chart**: Easy comparison of publisher performance
- **Impact Scoring**: Weighted scores based on retractions and citations
- **Tooltip Details**: Comprehensive publisher metrics

#### **Open Access Analysis**
- **Three-way Breakdown**: Open Access, Paywalled, Unknown
- **Statistical Icons**: Visual indicators with counts
- **Citation Impact**: How access status affects citation patterns

#### **Enhanced Problematic Papers Table**
- **Additional Columns**: Country, Institution, Access Status
- **Direct Links**: DOI, PubMed, paper detail buttons
- **Visual Indicators**: Color-coded access status badges
- **Progress Bars**: Citation rate visualization

## 🛠️ **Admin Interface**

### **Access Admin Panel**
Visit: `http://localhost:8000/admin/`

### **Enhanced Features**

#### **Retracted Papers Management**
- **Organized Fields**: Logical grouping by category
- **Enhanced Filters**: Country, Publisher, Article Type, Access Status
- **Visual Indicators**: 
  - 🔓 Open Access badges
  - 🔒 Paywalled indicators
  - ⚠️ Post-retraction citation warnings
- **Clickable Links**: Direct access to DOI, PubMed, retraction notices

#### **Bulk Operations**
- **Mark as Open Access**: Batch update access status
- **Mark as Paywalled**: Batch paywall status updates
- **Fetch Citations**: Queue citation updates for selected papers

#### **Advanced Search**
Search across all fields:
- Record ID, Title, Authors
- Journal, Publisher, Institution
- Subject, Country, DOI
- Retraction reason

## 📈 **Analytics Insights**

### **Geographic Analysis**
- **Country Performance**: Which countries have the most retractions
- **Open Access Rates**: Geographic patterns in open access adoption
- **Regional Trends**: How different regions handle retraction issues

### **Publisher Accountability**
- **Publisher Rankings**: Top publishers with retraction issues
- **Response Patterns**: How publishers handle retractions
- **Impact Scores**: Weighted metrics for publisher performance

### **Article Type Insights**
- **Type Distribution**: Research Articles vs Reviews vs Other
- **Citation Behavior**: How different article types perform post-retraction
- **Open Access Correlation**: Which article types are more likely to be open access

### **Access Status Impact**
- **Citation Patterns**: How paywalls affect post-retraction citations
- **Accessibility Metrics**: Open access adoption rates
- **Policy Insights**: Data for open access policy development

### **Institutional Analysis**
- **Problem Institutions**: Which institutions have the most retraction issues
- **Multi-institutional Papers**: Collaboration patterns in problematic research
- **Journal Diversity**: How many different journals institutions publish in

## 🔄 **Automated Daily Refresh**

### **Scheduled Tasks**
The system automatically:
- **Refreshes Retracted Papers**: Daily at 8:00 AM EST
- **Updates Citations**: Daily at 8:30 AM EST
- **Cleans Old Logs**: Weekly cleanup of import logs

### **Manual Refresh**
```bash
# Refresh retracted papers manually
python manage.py refresh_retracted_papers

# Fetch citations for all papers
python manage.py fetch_citations

# Fetch citations for specific paper
python manage.py fetch_citations --paper-id 12345
```

## 📊 **Business Intelligence Use Cases**

### **Research Integrity Monitoring**
- **Institution Oversight**: Track retraction patterns by institution
- **Publisher Accountability**: Monitor publisher response to retractions
- **Geographic Patterns**: Understand international research integrity trends

### **Policy Development**
- **Open Access Impact**: Data showing benefits of open access
- **Publisher Policies**: Evidence for publisher accountability measures
- **Institutional Guidelines**: Data for institutional retraction policies

### **Academic Research**
- **Citation Behavior**: Study how retractions affect scientific discourse
- **Disciplinary Patterns**: Understand retraction trends by research area
- **Timeline Analysis**: Track citation patterns over time post-retraction

## 🚀 **Getting Started**

### **1. Import Sample Data**
```bash
python manage.py import_retraction_watch sample_retraction_watch.csv
```

### **2. Explore Analytics**
Visit `http://localhost:8000/analytics/` and navigate through:
- Overview: Basic statistics and quick charts
- Trends: Time-based analysis with filtering
- Patterns: Advanced stratified analytics
- Network: Interactive relationship visualization

### **3. Admin Management**
Visit `http://localhost:8000/admin/` to:
- Browse imported papers with enhanced interface
- Use filters to find specific types of papers
- Perform bulk operations on paper collections
- Access direct links to external resources

### **4. Monitor System**
- Check scheduled task logs in admin
- Monitor import success rates
- Review citation fetch statistics

## 📋 **Best Practices**

### **Data Import**
- Always test with `--dry-run` first
- Use `--limit` for large datasets initially
- Enable `--update-existing` for data refreshes
- Monitor import logs for errors

### **Analytics Usage**
- Use time filters to focus on recent trends
- Cross-reference multiple chart types for insights
- Export data for external analysis when needed
- Monitor problematic papers table for urgent issues

### **Admin Management**
- Use bulk operations for efficiency
- Regularly update access status information
- Verify external links periodically
- Archive old import logs to maintain performance

## 🔍 **Troubleshooting**

### **Common Issues**
- **Date Format Errors**: Check CSV date format matches "M/D/YYYY 0:00"
- **Missing Fields**: Ensure all required CSV columns are present
- **Import Failures**: Check import logs in admin for detailed error messages
- **Chart Loading**: Ensure JavaScript is enabled and CDNs are accessible

### **Performance Optimization**
- Use pagination for large datasets
- Apply filters to reduce data load
- Clear browser cache if charts don't update
- Monitor database performance during imports

The enhanced CitingRetracted database now provides comprehensive research integrity analytics with professional-grade visualizations and management tools, making it an invaluable resource for researchers, publishers, and institutions monitoring retraction patterns and their ongoing impact on scientific literature. 