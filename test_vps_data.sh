#!/bin/bash
# Test the Raw Data Explorer and Model Diagnostics on VPS

echo "🔍 Testing Raw Data Explorer and Model Diagnostics on VPS"
echo "=========================================================="

# Test the data generation on production
DJANGO_SETTINGS_MODULE=citing_retracted.production_settings python3 debug_raw_data_explorer.py

echo ""
echo "🌐 Now test the democracy analysis page:"
echo "   https://prct.xeradb.com/democracy-analysis/"
echo ""
echo "Click on 'Raw Data Explorer' and 'Model Diagnostics' tabs to see if they display data."