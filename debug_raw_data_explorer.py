#!/usr/bin/env python3
"""
Debug script to test Raw Data Explorer and Model Diagnostics methods
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citing_retracted.settings')
django.setup()

from papers.views import DemocracyAnalysisView

def test_raw_data_explorer():
    print("🔍 Testing Raw Data Explorer method...")
    view = DemocracyAnalysisView()
    
    try:
        result = view._get_raw_data_explorer()
        print(f"✅ Raw Data Explorer returned: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📊 Keys: {list(result.keys())}")
            
            if 'variables' in result:
                print(f"📋 Variables count: {len(result['variables'])}")
                for var_name, var_data in list(result['variables'].items())[:3]:
                    print(f"   - {var_name}: {var_data.get('name', 'N/A')}")
            
            if 'sample_data' in result:
                print(f"📝 Sample data count: {len(result['sample_data'])}")
                if result['sample_data']:
                    print(f"   Sample keys: {list(result['sample_data'][0].keys())}")
            
            if 'coverage' in result:
                print(f"📈 Coverage stats: {result['coverage']}")
                
            if 'error' in result:
                print(f"❌ Error in result: {result['error']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing Raw Data Explorer: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_model_diagnostics():
    print("\n🔍 Testing Model Diagnostics method...")
    view = DemocracyAnalysisView()
    
    try:
        result = view._get_model_diagnostics()
        print(f"✅ Model Diagnostics returned: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📊 Keys: {list(result.keys())}")
            
            if 'convergence' in result:
                convergence = result['convergence']
                print(f"📋 Convergence title: {convergence.get('title', 'N/A')}")
                print(f"📋 Convergence metrics count: {len(convergence.get('metrics', []))}")
            
            if 'model_fit' in result:
                model_fit = result['model_fit']
                print(f"📋 Model fit title: {model_fit.get('title', 'N/A')}")
                print(f"📋 Model fit metrics count: {len(model_fit.get('metrics', []))}")
            
            if 'error' in result:
                print(f"❌ Error in result: {result['error']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing Model Diagnostics: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_analysis_context():
    print("\n🔍 Testing full analysis context...")
    view = DemocracyAnalysisView()
    
    try:
        context = view._get_analysis_context()
        print(f"✅ Analysis context returned: {type(context)}")
        print(f"📊 Context keys: {list(context.keys())}")
        
        if 'raw_data_explorer' in context:
            rde = context['raw_data_explorer']
            print(f"📋 Raw Data Explorer in context: {type(rde)}")
            if isinstance(rde, dict):
                print(f"   Keys: {list(rde.keys())}")
        
        if 'model_diagnostics' in context:
            md = context['model_diagnostics']
            print(f"📋 Model Diagnostics in context: {type(md)}")
            if isinstance(md, dict):
                print(f"   Keys: {list(md.keys())}")
        
        return context
        
    except Exception as e:
        print(f"❌ Error testing analysis context: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Starting debug tests...")
    
    # Test individual methods
    rde_result = test_raw_data_explorer()
    md_result = test_model_diagnostics()
    
    # Test full context
    context_result = test_analysis_context()
    
    print("\n🎯 Debug complete!")