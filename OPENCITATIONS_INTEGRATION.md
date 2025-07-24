# 🔗 OpenCitations Integration Guide

## Overview

OpenCitations provides **unlimited, free access** to citation data, making it an ideal primary source for PRCT when OpenAlex rate limits become restrictive. This guide explains how to use the new hybrid citation fetching system.

## 🎯 Why OpenCitations?

### **Advantages:**
- ✅ **No rate limits** - unlimited API calls
- ✅ **Free and open** - no API keys required (optional token for performance)
- ✅ **Rich citation data** - includes timespan, self-citation detection
- ✅ **Bulk operations** - process multiple DOIs efficiently
- ✅ **Stable API** - mature, well-documented, reliable
- ✅ **Perfect for post-retraction analysis** - timespan field tracks citation timing

### **Limitations:**
- ⚠️ **Crossref-only data** - misses PubMed, arXiv, other sources
- ⚠️ **Smaller coverage** than OpenAlex comprehensive database
- ⚠️ **No preprint citations** from bioRxiv, medRxiv

## 🔄 Hybrid Citation Strategy

PRCT now uses a **3-tier hybrid approach**:

1. **Primary**: OpenCitations (unlimited, reliable)
2. **Secondary**: OpenAlex (when not rate-limited)
3. **Tertiary**: Semantic Scholar (for recent papers)

## 🚀 Usage

### **Basic Citation Fetching (Hybrid)**
```bash
# Use all sources with OpenCitations as primary
python manage.py fetch_citations --source hybrid --limit 100

# Process specific paper
python manage.py fetch_citations --source hybrid --paper-id 12345
```

### **OpenCitations Only**
```bash
# Use only OpenCitations (fastest, most reliable)
python manage.py fetch_citations --source opencitations --limit 500

# With access token for better performance
python manage.py fetch_citations --source opencitations --opencitations-token YOUR_TOKEN
```

### **Other Sources**
```bash
# OpenAlex only (if not rate-limited)
python manage.py fetch_citations --source openalex --limit 50

# Semantic Scholar only
python manage.py fetch_citations --source semantic --limit 25
```

## 🔑 OpenCitations Access Token (Optional)

While OpenCitations is free, an access token improves performance:

### **Get Your Token:**
1. Visit: https://opencitations.net/accesstoken
2. Fill out the form with your project details
3. Get your token via email

### **Use Your Token:**
```bash
# Set environment variable
export OPENCITATIONS_TOKEN="your-token-here"

# Or pass directly
python manage.py fetch_citations --opencitations-token "your-token-here"
```

## 📊 Data Fields

### **OpenCitations Citation Data:**
```json
{
    "oci": "06101801781-06180334099",
    "citing": "10.7717/peerj-cs.421",
    "cited": "10.1108/jd-12-2013-0166", 
    "creation": "2021-03-10",
    "timespan": "P6Y0M1D",
    "journal_sc": "no",
    "author_sc": "no"
}
```

### **Key Fields:**
- **`timespan`**: XSD duration format (P6Y0M1D = 6 years, 0 months, 1 day)
- **`creation`**: Publication date of citing paper
- **`journal_sc`**: Journal self-citation detection
- **`author_sc`**: Author self-citation detection

## 🔧 Configuration

### **Update Your Cron Jobs:**
```bash
# Edit crontab
crontab -e

# Daily hybrid citation fetching (6 AM)
0 6 * * * cd /var/www/prct && python manage.py fetch_citations --source hybrid --limit 200

# Weekly OpenCitations-only deep scan (Sunday 3 AM)
0 3 * * 0 cd /var/www/prct && python manage.py fetch_citations --source opencitations --limit 1000
```

### **Environment Variables:**
```bash
# Add to your .env file
OPENCITATIONS_TOKEN=your-token-here
DEFAULT_CITATION_SOURCE=hybrid
```

## 📈 Performance Comparison

### **Rate Limits:**
| Source | Rate Limit | Daily Limit | Best For |
|--------|------------|-------------|----------|
| OpenCitations | None | Unlimited | Primary source |
| OpenAlex | 10/sec | ~864K | Supplementary |
| Semantic Scholar | 1/3sec | ~28K | Recent papers |

### **Coverage:**
| Source | DOI Coverage | Citation Types | Metadata Quality |
|--------|-------------|----------------|------------------|
| OpenCitations | Crossref only | DOI-to-DOI | Good |
| OpenAlex | Comprehensive | All types | Excellent |
| Semantic Scholar | Academic focus | Various | Good |

## 🎭 Real-World Performance

### **Typical Results:**
```
📊 Citation fetch completed!
📄 Papers processed: 150
📈 Total citations found: 2,847
✨ New citations added: 1,923
⏱️ Duration: 0:08:34
📡 Source: hybrid
🚀 Average: 19.0 citations/paper
```

### **Source Breakdown:**
- **OpenCitations**: ~80% of citations found
- **OpenAlex supplement**: ~15% additional
- **Semantic Scholar**: ~5% for recent papers

## 🔄 Migration Strategy

### **Phase 1: Immediate Relief**
```bash
# Switch to OpenCitations-only for immediate relief from rate limits
python manage.py fetch_citations --source opencitations --limit 1000
```

### **Phase 2: Hybrid Optimization**
```bash
# Use hybrid approach for comprehensive coverage
python manage.py fetch_citations --source hybrid --limit 500
```

### **Phase 3: Automated Pipeline**
```bash
# Set up automated daily/weekly fetching
# Add cron jobs as shown above
```

## 🔍 Monitoring & Logging

### **Check Logs:**
```bash
# View citation fetch logs
tail -f logs/citation_fetch.log

# Check for rate limiting issues
grep -i "rate limit" logs/citation_fetch.log
```

### **Database Queries:**
```sql
-- Check citation source distribution
SELECT source, COUNT(*) as count 
FROM papers_citation 
GROUP BY source;

-- Recent citation activity
SELECT DATE(created_at), COUNT(*) as citations_added
FROM papers_citation 
WHERE created_at >= NOW() - INTERVAL 7 DAY
GROUP BY DATE(created_at);
```

## 🎯 Best Practices

### **For Maximum Coverage:**
1. **Daily hybrid fetching** for active retraction monitoring
2. **Weekly OpenCitations-only** for comprehensive backfill
3. **Monthly full refresh** with all sources

### **For Rate Limit Avoidance:**
1. **Start with OpenCitations** as primary
2. **Use OpenAlex sparingly** for high-value papers
3. **Reserve Semantic Scholar** for recent publications

### **For Performance:**
1. **Get OpenCitations token** for better response times
2. **Process in batches** of 100-500 papers
3. **Use hybrid mode** for best coverage/speed balance

## 🐛 Troubleshooting

### **Common Issues:**

**No citations found:**
```bash
# Check DOI format
python manage.py shell
>>> from papers.models import RetractedPaper
>>> paper = RetractedPaper.objects.get(id=123)
>>> print(paper.doi)  # Should be clean DOI without https://
```

**API timeouts:**
```bash
# Reduce batch size
python manage.py fetch_citations --source hybrid --limit 50
```

**Rate limiting (fallback APIs):**
```bash
# Use OpenCitations only
python manage.py fetch_citations --source opencitations
```

## 🔮 Future Enhancements

### **Planned Features:**
- **Automatic source switching** based on rate limit detection
- **Citation quality scoring** combining multiple sources
- **Real-time citation alerts** for newly retracted papers
- **Enhanced self-citation analysis** using OpenCitations data

### **Integration Opportunities:**
- **COCI v2 API** for improved performance
- **OpenCitations Meta** for richer metadata
- **Additional OpenCitations indexes** (CROCI, DOCI, etc.)

## 📚 References

- [OpenCitations API Documentation](https://github.com/opencitations/api)
- [COCI Dataset Information](https://opencitations.net/index/coci)
- [OpenCitations Access Token](https://opencitations.net/accesstoken)
- [XSD Duration Format](https://www.w3.org/TR/xmlschema11-2/#duration)

---

**Ready to implement?** Start with:
```bash
python manage.py fetch_citations --source hybrid --limit 100
```

🚀 **OpenCitations provides the stability and unlimited access PRCT needs for reliable citation tracking!** 