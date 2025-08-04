#!/usr/bin/env python3
"""
Real-time Democracy Analysis Runner with Progress Tracking

This script runs the R democracy analysis with live progress updates
and detailed model information displayed in real-time.
"""

import subprocess
import sys
import time
import os
import threading
from queue import Queue, Empty

def print_progress_header():
    """Print a nice header for the analysis"""
    print("=" * 80)
    print("🎯 DEMOCRACY & RETRACTIONS: COMPREHENSIVE BAYESIAN ANALYSIS")
    print("📊 Real-time Progress Monitoring")
    print("⏱️ Started:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    print()

def monitor_r_output(process, output_queue):
    """Monitor R process output and put it in a queue"""
    for line in iter(process.stdout.readline, ''):
        if line:
            output_queue.put(('stdout', line.strip()))
    process.stdout.close()

def monitor_r_errors(process, output_queue):
    """Monitor R process errors and put them in a queue"""
    for line in iter(process.stderr.readline, ''):
        if line:
            output_queue.put(('stderr', line.strip()))
    process.stderr.close()

def format_output_line(line):
    """Format output lines with colors and structure"""
    line = line.strip()
    
    # Progress indicators
    if "[PROGRESS:" in line:
        return f"\n🚀 {line}\n"
    
    # Step headers
    elif "STEP " in line and ("BAYESIAN" in line or "SENSITIVITY" in line or "SUBGROUP" in line):
        return f"\n📋 {line}"
    
    # Model completion
    elif "✓ " in line and ("COMPLETED" in line or "completed in" in line):
        return f"✅ {line}"
    
    # Subgroup progress
    elif "[SUBGROUP " in line:
        return f"\n  🔬 {line}"
    
    # Individual model fitting
    elif "→ Fitting" in line:
        return f"    ⚙️ {line}"
    
    # Model diagnostics
    elif "R-hat:" in line or "ESS ratio:" in line or "LOO-CV" in line:
        return f"    📊 {line}"
    
    # Democracy effects (key results)
    elif "Democracy effect in" in line or "IRR =" in line:
        return f"    🎯 {line}"
    
    # System info
    elif "Available CPU cores:" in line or "Using" in line and "cores" in line:
        return f"    💻 {line}"
    
    # Errors
    elif "Error" in line:
        return f"❌ {line}"
    
    # Warnings
    elif "Warning" in line:
        return f"⚠️ {line}"
    
    # Time stamps
    elif "Time:" in line:
        return f"    🕐 {line}"
    
    # Completion messages
    elif "analysis completed" in line or "ANALYSIS COMPLETE" in line:
        return f"\n🎉 {line}"
    
    # Default
    else:
        return f"    {line}"

def run_analysis_with_progress():
    """Run the Django R analysis command with real-time progress"""
    
    print_progress_header()
    
    # Change to the Django project directory
    django_dir = "/Users/choxos/Documents/GitHub/CitingRetracted"
    os.chdir(django_dir)
    
    print(f"📁 Working directory: {django_dir}")
    print(f"🐍 Running Django management command...")
    print()
    
    # Start the Django R analysis command
    cmd = [sys.executable, "manage.py", "run_r_analysis"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Create queues for output
        output_queue = Queue()
        
        # Start monitoring threads
        stdout_thread = threading.Thread(
            target=monitor_r_output, 
            args=(process, output_queue)
        )
        stderr_thread = threading.Thread(
            target=monitor_r_errors, 
            args=(process, output_queue)
        )
        
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Process output in real-time
        start_time = time.time()
        
        while process.poll() is None:
            try:
                # Get output with a short timeout
                output_type, line = output_queue.get(timeout=0.1)
                
                if line:
                    formatted_line = format_output_line(line)
                    print(formatted_line)
                    sys.stdout.flush()
                    
            except Empty:
                # No output available, continue
                continue
        
        # Process any remaining output
        while not output_queue.empty():
            try:
                output_type, line = output_queue.get_nowait()
                if line:
                    formatted_line = format_output_line(line)
                    print(formatted_line)
            except Empty:
                break
        
        # Wait for threads to finish
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        
        # Get final return code
        return_code = process.wait()
        
        # Print final summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 80)
        if return_code == 0:
            print("🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
            print(f"⏱️ Total execution time: {duration/60:.1f} minutes")
            print(f"📄 Results file: r_analysis_output/r_analysis_results.json")
            print(f"📊 Summary file: r_analysis_output/summary_stats.json")
        else:
            print(f"❌ ANALYSIS FAILED (exit code: {return_code})")
            print(f"⏱️ Execution time: {duration/60:.1f} minutes")
        
        print("=" * 80)
        
        return return_code
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Analysis interrupted by user")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        return 1
        
    except Exception as e:
        print(f"\n❌ Error running analysis: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_analysis_with_progress()
    sys.exit(exit_code)