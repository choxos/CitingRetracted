# 🎨 PRCT Theme Migration Documentation

## 📋 Current Functionality to Preserve

### 🏠 **Home Page Features**
- **Statistics Cards**: Total papers, citations, recent retractions
- **Hero Section**: Gradient background (#667eea to #764ba2)
- **Navigation**: Home, Search, Analytics, Admin links
- **Responsive Design**: Mobile-friendly layout

### 📊 **Analytics Dashboard (77KB template!)**
**Tab Structure:**
1. **Overview Tab**
   - Summary statistics cards
   - Citation patterns pie chart
   - Post-retraction timeline

2. **Trends Tab**
   - Retraction trends over time (Line chart)
   - Citation comparison: Before vs After (Bar chart)
   - Subject distribution (Donut chart)

3. **Patterns Tab**
   - Citation heatmap (Custom HTML table)
   - Citation timing distribution (Line chart)
   - Journal impact analysis (Bubble chart)
   - Subject hierarchy sunburst (D3.js)
   - Geographic distribution (Plotly choropleth)
   - Article type analysis
   - Publisher analysis
   - Open access analysis

4. **Network Tab**
   - Interactive network analysis (D3.js force layout)

### 🎨 **Current Color Schemes**
```css
Primary Colors:
- Blue: #007bff
- Red: #dc3545 (retraction alerts)
- Green: #28a745
- Yellow: #ffc107

Gradients:
- Hero: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
- Dashboard tabs: linear-gradient(45deg, #007bff, #0056b3)

Chart Colors:
- primary: ['#007bff', '#6c757d', '#28a745', '#dc3545', '#ffc107', '#17a2b8']
- danger: ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#6f42c1', '#e83e8c']
- gradient: ['rgba(0,123,255,0.8)', 'rgba(40,167,69,0.8)', 'rgba(220,53,69,0.8)', 'rgba(255,193,7,0.8)']
```

### 🔧 **Interactive Features**
- **Auto-refresh controls**: 30s, 1min, 5min, 10min intervals
- **Real-time status indicators**: Last updated, loading spinners
- **Chart interactions**: Hover effects, zoom, pan
- **Filter controls**: Time range, network type
- **Responsive design**: Mobile-optimized layouts

### 📚 **JavaScript Libraries**
- **Chart.js**: Primary charting library
- **Plotly.js**: World map choropleth
- **D3.js**: Network visualization and sunburst charts
- **Bootstrap 5**: UI framework
- **jQuery**: DOM manipulation

### 🔍 **Search & Detail Pages**
- **Search filters**: Advanced filtering options
- **Paper detail**: Comprehensive paper information
- **Clickable elements**: Reason badges, subjects, authors
- **Citation timeline**: Visual citation history

### 📱 **Responsive Features**
- **Mobile navigation**: Collapsible navbar
- **Responsive charts**: Auto-resize functionality
- **Mobile-optimized tables**: Horizontal scrolling
- **Touch-friendly interactions**: Larger tap targets

## 🎯 **XeraDB Theme Integration Goals**

### ✅ **To Preserve**
- ALL 12+ visualization types
- Complete color scheme (keep colorful, professional)
- All interactive features
- Mobile responsiveness
- Auto-refresh functionality
- Real-time indicators

### 🔄 **To Migrate**
- Base template structure → XeraDB unified system
- CSS organization → Shared theme + PRCT overrides
- Navigation → XeraDB header pattern
- Footer → XeraDB footer pattern

### 🎨 **Theme Adaptation**
- Apply PRCT crimson red theme (#dc2626)
- Keep existing chart colors
- Maintain alert/warning color scheme
- Preserve gradient effects

## 📦 **Current File Structure**
```
templates/
├── base.html (10KB, 343 lines)
└── papers/
    ├── analytics.html (77KB, 1978 lines) ← CRITICAL
    ├── home.html (29KB, 507 lines)
    ├── paper_detail.html (31KB, 621 lines)
    └── search.html (23KB, 440 lines)

static/
└── images/
    ├── favicon.svg
    └── favicon.ico
```

## 🚨 **Critical Success Metrics**
1. **All charts render correctly** after migration
2. **All colors preserved** (colorful + professional)
3. **All interactions work** (hover, click, zoom)
4. **Mobile responsiveness maintained**
5. **Performance not degraded**
6. **Auto-refresh functionality intact**

---
*Created during XeraDB theme migration - preserve ALL current functionality* 