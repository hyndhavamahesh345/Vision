import json
import csv
import io
from typing import Dict, Any

def generate_json_report(aggregator_output: Dict[str, Any]) -> str:
    """Returns a JSON string of the report."""
    return json.dumps(aggregator_output, indent=2)

def generate_csv_report(aggregator_output: Dict[str, Any]) -> str:
    """Returns a CSV formatted string of the report inventory."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item Name", "Quantity"])
    
    for item in aggregator_output.get("inventory", []):
        writer.writerow([item["name"], item["quantity"]])
        
    return output.getvalue()
