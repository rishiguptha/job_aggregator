#!/bin/bash
cd "$(dirname "$0")"

echo "🚀 Job Aggregator Pipeline"
echo "=========================="
echo ""

echo "[] " > seen_jobs_v2.json
uv run python /Users/rishiguptha/Documents/03_Projects/job_aggregator/main.py --once --today

echo ""
echo "✅ Done! Press any key to close."
read -n 1 -s
