#!/bin/bash

# Full Competitive Intelligence Pipeline
# Executes scraping, analysis, and visualization in one command

echo "================================================================================"
echo "  COMPETITIVE INTELLIGENCE SYSTEM - FULL PIPELINE"
echo "================================================================================"
echo ""

# Set working directory
cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Scraping
echo "📡 STEP 1: Running scrapers..."
echo "--------------------------------------------------------------------------------"
python3 main.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Scraping completed successfully${NC}"
else
    echo -e "${RED}✗ Scraping failed${NC}"
    exit 1
fi
echo ""

# Check if data was generated
if [ ! -f "data/raw_data.csv" ]; then
    echo -e "${RED}✗ No data file generated${NC}"
    exit 1
fi

RECORD_COUNT=$(wc -l < data/raw_data.csv)
echo -e "${GREEN}✓ Generated $(($RECORD_COUNT - 1)) records${NC}"
echo ""

# Step 2: Analysis
echo "📊 STEP 2: Running analysis..."
echo "--------------------------------------------------------------------------------"
cd analysis
PYTHONPATH=.. python3 analyze.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Analysis completed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Analysis had warnings but continued${NC}"
fi
cd ..
echo ""

# Step 3: Visualizations
echo "📈 STEP 3: Generating visualizations..."
echo "--------------------------------------------------------------------------------"
cd analysis
PYTHONPATH=.. python3 visualize.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Visualizations generated${NC}"
else
    echo -e "${YELLOW}⚠ Some visualizations failed${NC}"
fi
cd ..
echo ""

# Summary
echo "================================================================================"
echo "  PIPELINE COMPLETE"
echo "================================================================================"
echo ""
echo "Generated Files:"
echo "  📄 Data:           data/raw_data.csv"
echo "  📊 Analysis:       analysis/tables/*.csv"
echo "  📈 Charts:         analysis/charts/*.png"
echo "  📝 Insights:       analysis/INSIGHTS.md"
echo "  📓 Report:         analysis/Competitive_Intelligence_Report.ipynb"
echo "  🪵 Logs:           logs/scraper.log"
echo ""
echo "Next Steps:"
echo "  1. Review insights: cat analysis/INSIGHTS.md"
echo "  2. View charts:     open analysis/charts/"
echo "  3. Open notebook:   jupyter notebook analysis/Competitive_Intelligence_Report.ipynb"
echo ""
echo "================================================================================"
