#!/usr/bin/env python3
"""
Treasure Insights Data Model API Helper

Fetches datamodel schema from Treasure Insights Reporting API and extracts
metrics, dimensions, and table relationships for Phase 1 prefilling.

Usage:
  python3 insights-api-helper.py <datamodel_name_or_id> [--region us|jp|eu|kr]

Example:
  python3 insights-api-helper.py sales_model --region us
  python3 insights-api-helper.py datamodel_123
"""

import json
import sys
import os
import re
from typing import Dict, List, Tuple, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip3 install requests")
    sys.exit(1)


# Regional API endpoints
ENDPOINTS = {
    "us": "https://api.treasuredata.com",
    "jp": "https://api.treasuredata.co.jp",
    "eu": "https://api.eu01.treasuredata.com",
    "kr": "https://api.ap02.treasuredata.com",
}


def get_api_key() -> str:
    """Extract TD API key from environment or tdx config."""
    if "TD_API_KEY" in os.environ:
        return os.environ["TD_API_KEY"]

    config_path = os.path.expanduser("~/.treasuredata/td.conf")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                if line.startswith("apikey"):
                    return line.split("=", 1)[1].strip()

    raise ValueError("API key not found. Set TD_API_KEY env var or run 'tdx auth setup'")


def get_endpoint(region: str = "us") -> str:
    """Get API endpoint for region."""
    region_lower = region.lower()
    if region_lower not in ENDPOINTS:
        raise ValueError(f"Unknown region: {region}. Must be one of: {list(ENDPOINTS.keys())}")
    return ENDPOINTS[region_lower]


def fetch_datamodel(datamodel_id: str, region: str = "us") -> Dict:
    """Fetch datamodel schema from Treasure Insights API."""
    api_key = get_api_key()
    endpoint = get_endpoint(region)
    url = f"{endpoint}/reporting/datamodels/{datamodel_id}"

    headers = {"Authorization": f"TD1 {api_key}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise ValueError(f"Datamodel '{datamodel_id}' not found")
        elif response.status_code == 401:
            raise ValueError("Unauthorized: invalid API key")
        else:
            raise ValueError(f"API error: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Network error: {str(e)}")


def extract_metrics(datamodel: Dict) -> List[Dict]:
    """Extract metrics (columns with aggregations) from datamodel."""
    metrics = []

    for dataset_group in datamodel.get("datasets", []):
        dataset = dataset_group.get("dataset", "")
        table = dataset_group.get("table", "")

        for column in dataset_group.get("columns", []):
            col_name = column.get("name", "")
            aggregations = column.get("aggregations", [])

            if aggregations:
                for agg in aggregations:
                    metric_name = f"{col_name.title()} ({agg.upper()})"
                    full_ref = f"{dataset}.{table}.{col_name}"
                    metrics.append({
                        "name": metric_name,
                        "column": col_name,
                        "table": table,
                        "dataset": dataset,
                        "aggregation": agg,
                        "formula": f"SUM({full_ref})" if agg == "sum" else f"AVG({full_ref})" if agg == "avg" else f"COUNT({full_ref})"
                    })

    return metrics


def extract_dimensions(datamodel: Dict) -> List[Dict]:
    """Extract dimensions (non-aggregation columns) from datamodel."""
    dimensions = []

    for dataset_group in datamodel.get("datasets", []):
        dataset = dataset_group.get("dataset", "")
        table = dataset_group.get("table", "")

        for column in dataset_group.get("columns", []):
            col_name = column.get("name", "")
            col_type = column.get("type", "").lower()
            aggregations = column.get("aggregations", [])

            # Include columns with no aggregations (dimensions)
            if not aggregations:
                dimensions.append({
                    "name": col_name.title(),
                    "column": col_name,
                    "table": table,
                    "dataset": dataset,
                    "type": col_type
                })

    return dimensions


def extract_relations(datamodel: Dict) -> List[Dict]:
    """Extract join relationships from datamodel."""
    relations = []

    for i, relation in enumerate(datamodel.get("relations", [])):
        definition = relation.get("definition", [])
        if len(definition) >= 2:
            left = definition[0]
            right = definition[1]

            relations.append({
                "id": i,
                "left_dataset": left.get("dataset", ""),
                "left_table": left.get("table", ""),
                "left_column": left.get("column", ""),
                "right_dataset": right.get("dataset", ""),
                "right_table": right.get("table", ""),
                "right_column": right.get("column", ""),
                "description": f"{left.get('table')}.{left.get('column')} → {right.get('table')}.{right.get('column')}"
            })

    return relations


def format_output(datamodel: Dict, metrics: List[Dict], dimensions: List[Dict], relations: List[Dict]) -> str:
    """Format extracted data for Phase 1 prefilling."""
    output = []

    output.append("# Treasure Insights Data Model Extraction\n")
    output.append(f"**Model Name:** {datamodel.get('name', 'Unknown')}")
    output.append(f"**Model ID:** {datamodel.get('id', 'Unknown')}\n")

    # Metrics
    output.append("## Discovered Metrics\n")
    if metrics:
        for m in metrics:
            output.append(f"- **{m['name']}** ({m['dataset']}.{m['table']}.{m['column']})")
            output.append(f"  - Formula suggestion: `{m['formula']}`")
    else:
        output.append("*(No metrics found with aggregations configured)*\n")

    # Dimensions
    output.append("\n## Discovered Dimensions\n")
    if dimensions:
        for d in dimensions:
            output.append(f"- **{d['name']}** ({d['dataset']}.{d['table']}.{d['column']}) — {d['type']}")
    else:
        output.append("*(No dimensions found)*\n")

    # Relations
    output.append("\n## Discovered Join Relationships\n")
    if relations:
        for r in relations:
            output.append(f"- {r['description']}")
    else:
        output.append("*(No relations found)*\n")

    # JSON output
    output.append("\n## Raw JSON Output\n")
    output.append("```json")
    output.append(json.dumps({
        "datamodel_name": datamodel.get("name"),
        "datamodel_id": datamodel.get("id"),
        "metrics_count": len(metrics),
        "dimensions_count": len(dimensions),
        "relations_count": len(relations),
        "metrics": metrics,
        "dimensions": dimensions,
        "relations": relations
    }, indent=2))
    output.append("```")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    datamodel_id = sys.argv[1]
    region = "us"

    # Parse optional --region flag
    if "--region" in sys.argv:
        idx = sys.argv.index("--region")
        if idx + 1 < len(sys.argv):
            region = sys.argv[idx + 1]

    try:
        print(f"Fetching datamodel '{datamodel_id}' from region '{region}'...\n")
        datamodel = fetch_datamodel(datamodel_id, region)

        metrics = extract_metrics(datamodel)
        dimensions = extract_dimensions(datamodel)
        relations = extract_relations(datamodel)

        output = format_output(datamodel, metrics, dimensions, relations)
        print(output)

        # Also save to JSON file for Phase 1 to consume
        json_output = {
            "datamodel_name": datamodel.get("name"),
            "datamodel_id": datamodel.get("id"),
            "metrics": metrics,
            "dimensions": dimensions,
            "relations": relations
        }

        filename = f"insights_datamodel_{datamodel_id}.json"
        with open(filename, "w") as f:
            json.dump(json_output, f, indent=2)
        print(f"\n✓ Saved to {filename}")

    except ValueError as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
