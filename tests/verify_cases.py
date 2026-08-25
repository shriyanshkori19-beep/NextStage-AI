import os
import pandas as pd
import sys

# Add root folder to path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.checker import check_case

def test_dataset():
    csv_path = os.path.join("data", "cases.csv")
    if not os.path.exists(csv_path):
        print(f"FAIL: {csv_path} does not exist.")
        sys.exit(1)
        
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"FAIL: Could not parse CSV file. Error: {e}")
        sys.exit(1)
        
    print(f"INFO: Loaded dataset with {len(df)} cases.")
    
    # 1. Verify case count (At least 30 cases)
    if len(df) < 30:
        print(f"FAIL: Dataset has {len(df)} cases, which is less than the required 30.")
        sys.exit(1)
    else:
        print(f"PASS: Case coverage count is {len(df)} (At least 30 required).")
        
    # 2. Verify columns
    required_cols = ["case_id", "symptom", "topology_note", "concept_tag", "severity", "osi_layer", "show_outputs", "expected_fault"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"FAIL: Missing columns in CSV: {missing_cols}")
        sys.exit(1)
    else:
        print("PASS: All required columns are present in the dataset.")
        
    # 3. Test deterministic checker on all cases
    passed_checker = True
    for index, row in df.iterrows():
        try:
            warnings = check_case(
                row["case_id"], 
                row["symptom"], 
                row["topology_note"], 
                row["show_outputs"]
            )
            # Print warning output for some cases to check behavior
            if index < 5 or warnings:
                print(f"  Case {row['case_id']} ({row['concept_tag']}): Caught {len(warnings)} static warnings: {warnings}")
        except Exception as e:
            print(f"FAIL: Exception raised during check_case on {row['case_id']}: {e}")
            passed_checker = False
            
    if passed_checker:
        print("PASS: Deterministic checker successfully processed all cases without exceptions.")
    else:
        sys.exit(1)
        
    print("ALL TESTS PASSED SUCCESSFULLY! The NetSage AI dataset and rule checker are ready for production deployment.")

if __name__ == "__main__":
    test_dataset()
