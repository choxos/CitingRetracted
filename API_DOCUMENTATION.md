# PRCT API Documentation

**Papers Citing Retracted Texts (PRCT) - REST API Reference**

Version: 1.0  
Base URL: `https://prct.xeradb.com`  
Last Updated: January 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Response Format](#response-format)
5. [Error Handling](#error-handling)
6. [API Endpoints](#api-endpoints)
   - [Search & Discovery](#search--discovery)
   - [Paper Data](#paper-data)
   - [Analytics](#analytics)
   - [Data Export](#data-export)
   - [Utility](#utility)
7. [Code Examples](#code-examples)
8. [SDK & Libraries](#sdk--libraries)

---

## Overview

The PRCT API provides programmatic access to retracted paper data, citation analysis, and comprehensive analytics. All endpoints return JSON responses and support various query parameters for filtering and customization.

### Key Features
- **Retracted Paper Database**: Access to 65,000+ retracted papers from Retraction Watch
- **Citation Analysis**: Post-retraction citation tracking and timeline analysis
- **Real-time Analytics**: Live statistics and trending data
- **Advanced Filtering**: Multi-dimensional filtering by journal, subject, date, etc.
- **Export Capabilities**: JSON and CSV data export options

---

## Authentication

Currently, the PRCT API is **public** and does not require authentication. All endpoints are accessible without API keys.

> **Note**: Rate limiting is applied to prevent abuse. See [Rate Limiting](#rate-limiting) section.

---

## Rate Limiting

- **General Endpoints**: 100 requests per minute per IP
- **Export Endpoints**: 10 requests per minute per IP
- **Analytics Endpoints**: 50 requests per minute per IP

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Response Format

All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "timestamp": "2025-01-16T10:30:00Z",
    "version": "1.0"
  }
}
```

### Paginated Response
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1250,
    "total_pages": 63
  },
  "meta": {
    "timestamp": "2025-01-16T10:30:00Z",
    "version": "1.0"
  }
}
```

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Request succeeded
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'record_id' parameter is required",
    "details": {
      "parameter": "record_id",
      "received": null,
      "expected": "string"
    }
  },
  "meta": {
    "timestamp": "2025-01-16T10:30:00Z",
    "version": "1.0"
  }
}
```

---

## API Endpoints

### Search & Discovery

#### 🔍 Search Autocomplete
Get search suggestions for papers and authors.

**Endpoint**: `GET /api/search-autocomplete/`

**Parameters**:
- `q` (string, required): Search query (minimum 3 characters)

**Example Request**:
```bash
GET /api/search-autocomplete/?q=covid
```

**Example Response**:
```json
{
  "suggestions": [
    {
      "title": "COVID-19 vaccine effectiveness study",
      "author": "Smith, J.; Johnson, A.",
      "journal": "Nature Medicine",
      "record_id": "RW12345",
      "url": "/paper/RW12345/",
      "post_retraction_citations": 15
    }
  ]
}
```

---

### Paper Data

#### 📄 Paper Citations
Get detailed citation data for a specific retracted paper.

**Endpoint**: `GET /api/paper/<record_id>/citations/`

**Parameters**:
- `record_id` (string, required): Retraction Watch record ID

**Example Request**:
```bash
GET /api/paper/RW12345/citations/
```

**Example Response**:
```json
{
  "citations_by_year": {
    "2020": 45,
    "2021": 67,
    "2022": 89,
    "2023": 23
  },
  "post_retraction_by_year": {
    "2020": 0,
    "2021": 12,
    "2022": 34,
    "2023": 23
  },
  "timeline_data": [
    {
      "days_after": 120,
      "citing_paper": "Analysis of retracted study impact",
      "publication_date": "2021-05-15",
      "is_post_retraction": true
    }
  ],
  "post_retraction_stats": {
    "within_30_days": 5,
    "within_1_year": 28,
    "within_2_years": 42,
    "after_2_years": 12
  },
  "total_citations": 224,
  "post_retraction_count": 69
}
```

---

### Analytics

#### 📊 Post-Retraction Analytics
Get comprehensive post-retraction citation analytics with filtering.

**Endpoint**: `GET /api/post-retraction-analytics/`

**Parameters**:
- `time_filter` (string, optional): Filter by time period
  - Values: `all`, `1y`, `3y`, `5y`
  - Default: `all`
- `journal` (string, optional): Filter by journal name (partial match)
- `subject` (string, optional): Filter by subject area (partial match)

**Example Request**:
```bash
GET /api/post-retraction-analytics/?time_filter=1y&journal=nature
```

**Example Response**:
```json
{
  "total_post_retraction": 15420,
  "time_distribution": {
    "within_30_days": 1250,
    "within_6_months": 4890,
    "within_1_year": 8920,
    "within_2_years": 12650,
    "after_2_years": 2770
  },
  "monthly_trend": [
    {
      "month": "2024-01",
      "count": 145
    },
    {
      "month": "2024-02", 
      "count": 167
    }
  ],
  "filters_applied": {
    "time_filter": "1y",
    "journal_filter": "nature",
    "subject_filter": ""
  }
}
```

#### 📈 Analytics Data (Comprehensive)
Get comprehensive analytics data with advanced filtering and aggregation.

**Endpoint**: `GET /api/analytics-data/`

**Parameters**:
- `type` (string, optional): Type of analytics data
  - Values: `overview`, `trends`, `citations`, `subjects`, `geographic`
  - Default: `overview`
- `format` (string, optional): Response format
  - Values: `json`, `csv`
  - Default: `json`

**Example Request**:
```bash
GET /api/analytics-data/?type=overview
```

**Example Response**:
```json
{
  "total_papers": 65432,
  "total_citations": 1234567,
  "post_retraction_citations": 89012,
  "post_retraction_rate": 7.2,
  "recent_papers": 456,
  "top_subjects": [
    {
      "subject": "Medicine",
      "count": 12450
    },
    {
      "subject": "Biology",
      "count": 8920
    }
  ],
  "cache_timestamp": "2025-01-16T10:30:00Z"
}
```

#### ⚡ Real-time Analytics
Get real-time analytics data for dashboards and monitoring.

**Endpoint**: `GET /api/analytics-realtime/`

**Cache**: 1 minute

**Example Request**:
```bash
GET /api/analytics-realtime/
```

**Example Response**:
```json
{
  "stats": {
    "total_papers": 65432,
    "total_citations": 1234567,
    "post_retraction_citations": 89012,
    "recent_retractions": 23
  },
  "recent_activity": {
    "total_imports": 3,
    "records_imported": 245
  },
  "citation_patterns": {
    "post_retraction": 89012,
    "pre_retraction": 1145555,
    "same_day": 0
  },
  "last_updated": "2025-01-16T10:30:00Z",
  "status": "success"
}
```

#### 🎯 Optimized Analytics API
High-performance analytics endpoint with built-in caching.

**Endpoint**: `GET /api/analytics/`

**Parameters**:
- `type` (string, required): Type of analytics data
  - Values: `overview`, `trends`, `citations`, `subjects`, `geographic`

**Cache**: 5 minutes

**Example Request**:
```bash
GET /api/analytics/?type=subjects
```

**Example Response**:
```json
{
  "subjects": [
    {
      "subject": "Medicine - Clinical Research",
      "count": 8920,
      "avg_citations": 45.2
    },
    {
      "subject": "Biology - Cell Biology", 
      "count": 6780,
      "avg_citations": 38.9
    }
  ],
  "total_subjects": 156,
  "cache_timestamp": "2025-01-16T10:25:00Z"
}
```

---

### Data Export

#### 💾 Export Data
Export retracted papers data with post-retraction analytics.

**Endpoint**: `GET /api/export/`

**Parameters**:
- `format` (string, optional): Export format
  - Values: `json`, `csv`, `excel`
  - Default: `json`
- `limit` (integer, optional): Number of records to export
  - Default: `1000`
  - Maximum: `10000`

**Example Request**:
```bash
GET /api/export/?format=json&limit=100
```

**Example Response**:
```json
{
  "papers": [
    {
      "record_id": "RW12345",
      "title": "COVID-19 vaccine effectiveness study",
      "author": "Smith, J.; Johnson, A.",
      "journal": "Nature Medicine",
      "retraction_date": "2021-03-15",
      "total_citations": 224,
      "post_retraction_citations": 69,
      "post_retraction_percentage": 30.8,
      "reason": "Data fabrication"
    }
  ]
}
```

---

### Utility

#### 🔥 Warm Cache
Warm up application caches to improve performance.

**Endpoint**: `POST /api/warm-cache/`

**Parameters**:
- `type` (string, optional): Type of cache to warm
  - Values: `analytics`, `all`
  - Default: `all`

**Example Request**:
```bash
POST /api/warm-cache/
Content-Type: application/json

{
  "type": "analytics"
}
```

**Example Response**:
```json
{
  "status": "success",
  "message": "Cache warmed successfully"
}
```

---

## Code Examples

### JavaScript/Node.js

```javascript
// Get paper citations
async function getPaperCitations(recordId) {
  const response = await fetch(`https://prct.xeradb.com/api/paper/${recordId}/citations/`);
  const data = await response.json();
  
  console.log(`Total citations: ${data.total_citations}`);
  console.log(`Post-retraction citations: ${data.post_retraction_count}`);
  
  return data;
}

// Search autocomplete
async function searchPapers(query) {
  const response = await fetch(`https://prct.xeradb.com/api/search-autocomplete/?q=${encodeURIComponent(query)}`);
  const data = await response.json();
  
  return data.suggestions;
}

// Get analytics overview
async function getAnalyticsOverview() {
  const response = await fetch('https://prct.xeradb.com/api/analytics/?type=overview');
  const data = await response.json();
  
  return data;
}
```

### Python

```python
import requests
import json

class PRCTClient:
    def __init__(self, base_url="https://prct.xeradb.com"):
        self.base_url = base_url
        
    def get_paper_citations(self, record_id):
        """Get citation data for a specific paper"""
        url = f"{self.base_url}/api/paper/{record_id}/citations/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def search_autocomplete(self, query):
        """Get search suggestions"""
        url = f"{self.base_url}/api/search-autocomplete/"
        params = {"q": query}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()["suggestions"]
    
    def get_analytics(self, data_type="overview"):
        """Get analytics data"""
        url = f"{self.base_url}/api/analytics/"
        params = {"type": data_type}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def export_data(self, format="json", limit=1000):
        """Export papers data"""
        url = f"{self.base_url}/api/export/"
        params = {"format": format, "limit": limit}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

# Usage example
client = PRCTClient()

# Get citations for a specific paper
citations = client.get_paper_citations("RW12345")
print(f"Post-retraction citations: {citations['post_retraction_count']}")

# Search for papers
suggestions = client.search_autocomplete("covid")
for paper in suggestions:
    print(f"{paper['title']} - {paper['journal']}")

# Get analytics overview
analytics = client.get_analytics("overview")
print(f"Total papers: {analytics['total_papers']}")
```

### cURL

```bash
# Get paper citations
curl -X GET "https://prct.xeradb.com/api/paper/RW12345/citations/" \
  -H "Accept: application/json"

# Search autocomplete
curl -X GET "https://prct.xeradb.com/api/search-autocomplete/?q=covid" \
  -H "Accept: application/json"

# Get post-retraction analytics with filters
curl -X GET "https://prct.xeradb.com/api/post-retraction-analytics/?time_filter=1y&journal=nature" \
  -H "Accept: application/json"

# Export data
curl -X GET "https://prct.xeradb.com/api/export/?format=json&limit=100" \
  -H "Accept: application/json"

# Warm cache
curl -X POST "https://prct.xeradb.com/api/warm-cache/" \
  -H "Content-Type: application/json" \
  -d '{"type": "analytics"}'
```

### R

```r
library(httr)
library(jsonlite)

# PRCT API client for R
get_paper_citations <- function(record_id, base_url = "https://prct.xeradb.com") {
  url <- paste0(base_url, "/api/paper/", record_id, "/citations/")
  response <- GET(url)
  stop_for_status(response)
  return(content(response, "parsed"))
}

search_autocomplete <- function(query, base_url = "https://prct.xeradb.com") {
  url <- paste0(base_url, "/api/search-autocomplete/")
  response <- GET(url, query = list(q = query))
  stop_for_status(response)
  return(content(response, "parsed")$suggestions)
}

get_analytics <- function(type = "overview", base_url = "https://prct.xeradb.com") {
  url <- paste0(base_url, "/api/analytics/")
  response <- GET(url, query = list(type = type))
  stop_for_status(response)
  return(content(response, "parsed"))
}

# Usage
citations <- get_paper_citations("RW12345")
cat("Post-retraction citations:", citations$post_retraction_count, "\n")

suggestions <- search_autocomplete("covid")
for (paper in suggestions) {
  cat(paper$title, "-", paper$journal, "\n")
}
```

---

## SDK & Libraries

### Official Libraries
- **Python SDK**: `pip install prct-api-client` (Coming Soon)
- **JavaScript SDK**: `npm install prct-api-client` (Coming Soon)
- **R Package**: `install.packages("prctapi")` (Coming Soon)

### Community Libraries
- **Go Client**: [github.com/example/prct-go-client](https://github.com/example/prct-go-client)
- **PHP Client**: [packagist.org/packages/prct/api-client](https://packagist.org/packages/prct/api-client)

---

## Support & Contact

- **Documentation**: [https://prct.xeradb.com/docs/](https://prct.xeradb.com/docs/)
- **Issues**: [https://github.com/xeradb/prct/issues](https://github.com/xeradb/prct/issues)
- **Email**: support@xeradb.com
- **Status Page**: [https://status.xeradb.com](https://status.xeradb.com)

---

## Changelog

### Version 1.0 (January 2025)
- Initial API release
- 8 core endpoints
- JSON response format
- Rate limiting implementation
- Comprehensive documentation

---

**© 2025 XeraDB. All rights reserved.** 