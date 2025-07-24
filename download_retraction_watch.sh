#!/bin/bash

# Download Latest Retraction Watch Data
# Simple script to fetch the retraction database

echo "🎯 Downloading Latest Retraction Watch Data..."
echo "================================================"

# Create timestamp for filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="retraction_watch_${TIMESTAMP}.csv"

# Primary URLs to try
URLS=(
    "http://retractiondatabase.org/RetractionWatch.csv"
    "https://api.crossref.org/works?filter=type:retraction&rows=1000&mailto=your-email@domain.com"
    "http://retractiondatabase.org/download/"
)

# Function to download and validate CSV
download_csv() {
    local url=$1
    local output_file=$2
    
    echo "📡 Trying: $url"
    
    # Download with curl
    if curl -L -A "Mozilla/5.0 (compatible; PRCT-Bot/1.0)" \
        --connect-timeout 30 \
        --max-time 300 \
        -o "$output_file" \
        "$url" 2>/dev/null; then
        
        # Check if file exists and has content
        if [[ -s "$output_file" ]]; then
            # Validate CSV by checking first line
            FIRST_LINE=$(head -n1 "$output_file")
            if [[ "$FIRST_LINE" == *","* ]]; then
                LINES=$(wc -l < "$output_file")
                echo "✅ Downloaded: $output_file ($LINES lines)"
                return 0
            else
                echo "⚠️  File doesn't appear to be CSV format"
                rm -f "$output_file"
            fi
        else
            echo "❌ Download failed or empty file"
            rm -f "$output_file"
        fi
    else
        echo "❌ Curl failed"
        rm -f "$output_file"
    fi
    
    return 1
}

# Try each URL
for url in "${URLS[@]}"; do
    if download_csv "$url" "$FILENAME"; then
        echo ""
        echo "🎉 Success! Downloaded: $FILENAME"
        echo "📊 Preview:"
        head -n5 "$FILENAME" | cut -c1-100
        echo ""
        echo "📁 File ready for import into PRCT database"
        exit 0
    fi
done

echo ""
echo "❌ Could not download from any source"
echo "🔧 Manual alternatives:"
echo "   1. Visit: http://retractiondatabase.org/"
echo "   2. Register for free account if required"
echo "   3. Download CSV manually"
echo "   4. Check if site is temporarily down"

exit 1 