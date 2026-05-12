import subprocess
import sys
import os

def run_script(script_name, args=""):
    """
    Runs a sub-script using the same Python interpreter as the orchestrator.
    This bypasses Mac/Bash alias issues like 'python' vs 'python3'.
    """
    # sys.executable ensures we use the exact same python path currently in use
    python_exe = sys.executable
    
    # We wrap the command in quotes to handle any potential spaces in folder names
    command = f'"{python_exe}" {script_name} {args}'
    
    print(f"\n[RUNNING]: {command}")
    print("-" * 60)
    
    # Run the command
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ ERROR: '{script_name}' failed with exit code {result.returncode}.")
        print("Stopping the pipeline to prevent data mismatch.")
        sys.exit(1)
        
    print(f"✅ SUCCESS: '{script_name}' completed successfully.")

def main():
    # Get the current directory name for the header
    current_dir = os.path.basename(os.getcwd())
    
    print("=" * 70)
    print(f"🚀 AI PIPELINE ORCHESTRATOR | FOLDER: {current_dir}")
    print("=" * 70)

    # 1. ANALYZE PROMPT DRIFT
    # Compares prompts_baseline.json vs prompts.json
    run_script("prompt_drift.py")

    # 2. GENERATE NEW RESPONSES
    # Uses prompts.json to call OpenAI API
    run_script("prompts.py")

    # 3. ANALYZE RESPONSE DRIFT
    # Compares baseline response vs newest response
    # We include --ignore-punctuation to reduce false drift alerts
    run_script("response_drift.py", "--ignore-punctuation")

    print("\n" + "=" * 70)
    print("🎉 FULL PIPELINE SUCCESSFUL")
    print("-" * 70)
    print(f"Time: {subprocess.check_output('date').decode().strip()}")
    print("Reports Generated:")
    print("  📁 prompt_drift_report.html")
    print("  📁 response_drift_report.html")
    print("=" * 70)

if __name__ == "__main__":
    main()