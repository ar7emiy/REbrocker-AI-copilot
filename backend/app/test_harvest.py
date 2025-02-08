from homeharvest import scrape_property
import pandas as pd

# Test address
test_address = "2427 N Greenview, Chicago, IL 60614"

try:
    # Get property data
    result = scrape_property(location=test_address)
    
    # Convert to DataFrame if it isn't already
    if not isinstance(result, pd.DataFrame):
        result = pd.DataFrame([result])
    
    # Show column names
    print("\nColumns:", result.columns.tolist())
    
    # Show first row of data
    print("\nSample Data:")
    print(result.iloc[0].to_dict())
    
except Exception as e:
    print(f"Error: {str(e)}")