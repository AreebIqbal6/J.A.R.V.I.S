import requests

def GetEarthEvents(query):
    """Fetches real-time natural disaster telemetry from NASA EONET v3."""
    
    # Map spoken words to NASA's official v3 category IDs
    query_lower = query.lower()
    category = ""
    
    if "fire" in query_lower:
        category = "wildfires"
    elif "volcano" in query_lower or "eruption" in query_lower:
        category = "volcanoes"
    elif "storm" in query_lower or "hurricane" in query_lower or "cyclone" in query_lower:
        category = "severeStorms"
    elif "ice" in query_lower or "iceberg" in query_lower:
        category = "seaLakeIce"
        
    # NASA EONET v3 API Endpoint
    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    
    # Parameters: Only open events, limit to 4 so Jarvis doesn't talk forever
    params = {
        "status": "open",
        "limit": 4
    }
    
    if category:
        params["category"] = category

    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return "Sir, the NASA telemetry link is currently experiencing interference."
            
        data = response.json()
        events = data.get("events", [])
        
        if not events:
            if category:
                return f"Sir, NASA is not currently tracking any major open events in the {category} category."
            else:
                return "NASA's Earth Observatory reports no major anomalous events at this time, sir."
                
        # Format the data for Text-To-Speech
        report = "Here is the latest telemetry from NASA's Earth Observatory: "
        for i, event in enumerate(events):
            title = event.get("title", "Unknown Event")
            report += f"{i+1}, {title}. "
            
        return report.strip()

    except Exception as e:
        return f"NASA satellite uplink failed, sir. Error: {e}"