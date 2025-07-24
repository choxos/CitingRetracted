#!/bin/bash

# Download Latest Retraction Watch Data
# Simple script to fetch the retraction database

echo "🎯 Downloading Latest Retraction Watch Data..."
echo "================================================"

# Create timestamp for filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="retraction_watch_${TIMESTAMP}.csv"

# Primary URL - ONLY official source
URL="https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv?ref_type=heads&inline=false"

# Function to download and validate CSV
download_csv() {
    local url=$1
    local output_file=$2
    
    echo "📡 Downloading from official GitLab source..."
    echo "🔗 URL: $url"
    
    # Download with wget -c (resumable download)
    if wget -c -T 30 --progress=bar \
        --user-agent="PRCT-DataBot/1.0" \
        -O "$output_file" \
        "$url" 2>&1; then
        
        # Check if file exists and has content
        if [[ -s "$output_file" ]]; then
            # Validate CSV by checking first line
            FIRST_LINE=$(head -n1 "$output_file")
            if [[ "$FIRST_LINE" == *"Record ID"* ]]; then
                LINES=$(wc -l < "$output_file")
                echo "✅ Downloaded: $output_file ($LINES lines)"
                return 0
            else
                echo "⚠️  File doesn't appear to be valid Retraction Watch CSV"
                echo "First line: $FIRST_LINE"
                rm -f "$output_file"
            fi
        else
            echo "❌ Download failed or empty file"
            rm -f "$output_file"
        fi
    else
        echo "❌ wget failed"
        rm -f "$output_file"
    fi
    
    return 1
}

# Try each URL
if download_csv "$URL" "$FILENAME"; then
    echo ""
    echo "🎉 Success! Downloaded: $FILENAME"
    echo "📊 Preview:"
    head -n5 "$FILENAME" | cut -c1-100
    echo ""
    echo "📁 File ready for import into PRCT database"
    exit 0
else
    echo ""
    echo "❌ Could not download from any source"
    echo "🔧 Manual alternatives:"
    echo "   1. Visit: http://retractiondatabase.org/"
    echo "   2. Register for free account if required"
    echo "   3. Download CSV manually"
    echo "   4. Check if site is temporarily down"

    exit 1
fi 