"""
Backend/GeoSleuth.py
OSINT Geolocation & Tactical Coordinate Recon Engine
Inspired by Oldcircle/geo-sleuth (https://github.com/Oldcircle/geo-sleuth)
Leverages OpenStreetMap Nominatim, IP intelligence, and image EXIF GPS extraction.
Emits map targeting commands directly to J.A.R.V.I.S. Tactical GIS Map.
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

logger = logging.getLogger("JARVIS_GeoSleuth")

USER_AGENT = "JARVIS-Autonomous-AI/2.0 (Tactical Recon Core; contact: areeb@jarvis.ai)"

def geocode_place(query: str) -> Dict[str, Any]:
    """
    Forward geocodes a location query using OpenStreetMap Nominatim.
    Returns latitude, longitude, bounding box, and tactical intelligence summary.
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty."}

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query.strip(),
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=5.0)
        data = res.json()
        if not data or len(data) == 0:
            return {"error": f"No tactical coordinates found for location: '{query}'."}

        target = data[0]
        lat = float(target.get("lat", 0.0))
        lon = float(target.get("lon", 0.0))
        display_name = target.get("display_name", "")
        place_type = target.get("type", "landmark")
        boundingbox = target.get("boundingbox", [])

        return {
            "status": "TARGET_LOCKED",
            "query": query,
            "display_name": display_name,
            "lat": lat,
            "lon": lon,
            "type": place_type,
            "boundingbox": boundingbox,
            "osm_id": target.get("osm_id"),
            "osm_url": f"https://www.openstreetmap.org/#map=16/{lat}/{lon}",
            "summary": f"Target acquired: {display_name} ({lat:.5f}, {lon:.5f})"
        }
    except Exception as e:
        logger.error(f"Geocoding error for '{query}': {e}")
        return {"error": f"OSINT reconnaissance failed: {str(e)}"}

def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    """
    Reverse geocodes latitude/longitude coordinates to an exact address and landmark.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(url, params=params, headers=headers, timeout=5.0)
        data = res.json()
        if not data or "error" in data:
            return {"error": "Coordinates resolution failed."}

        display_name = data.get("display_name", "")
        address = data.get("address", {})

        return {
            "status": "TARGET_RESOLVED",
            "lat": lat,
            "lon": lon,
            "display_name": display_name,
            "city": address.get("city") or address.get("town") or address.get("county"),
            "country": address.get("country"),
            "postcode": address.get("postcode"),
            "summary": f"Tactical coordinate: {display_name}"
        }
    except Exception as e:
        return {"error": str(e)}

def geolocate_ip(ip_address: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs IP Geolocation lookup via ip-api.
    If ip_address is None or 'myip', resolves client's public egress IP.
    """
    target = ip_address.strip() if ip_address and ip_address.strip() != "myip" else ""
    url = f"http://ip-api.com/json/{target}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"

    try:
        res = requests.get(url, timeout=4.0)
        data = res.json()
        if data.get("status") != "success":
            return {"error": data.get("message", "IP geolocation resolution failed.")}

        lat = float(data.get("lat", 0.0))
        lon = float(data.get("lon", 0.0))
        city = data.get("city", "")
        country = data.get("country", "")
        isp = data.get("isp", "")
        ip_query = data.get("query", "")

        return {
            "status": "IP_TARGET_LOCKED",
            "ip": ip_query,
            "city": city,
            "region": data.get("regionName", ""),
            "country": country,
            "lat": lat,
            "lon": lon,
            "isp": isp,
            "org": data.get("org", ""),
            "timezone": data.get("timezone", ""),
            "summary": f"IP {ip_query} localized to {city}, {country} ({lat:.4f}, {lon:.4f}) via {isp}"
        }
    except Exception as e:
        return {"error": str(e)}

geocode_ip = geolocate_ip

def extract_exif_gps(image_path: str) -> Dict[str, Any]:

    """
    Extracts GPS latitude/longitude metadata from an image file (JPEG/TIFF).
    """
    try:
        image = Image.open(image_path)
        exif_raw = image._getexif()
        if not exif_raw:
            return {"error": "No EXIF metadata present in image."}

        gps_info = {}
        for tag, value in exif_raw.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for gps_tag, gps_value in value.items():
                    sub_name = GPSTAGS.get(gps_tag, gps_tag)
                    gps_info[sub_name] = gps_value

        if not gps_info:
            return {"error": "Image contains EXIF data but lacks GPS coordinate tags."}

        def dms_to_decimal(dms, ref):
            deg = float(dms[0])
            minute = float(dms[1])
            second = float(dms[2])
            dec = deg + (minute / 60.0) + (second / 3600.0)
            if ref in ['S', 'W']:
                dec = -dec
            return dec

        lat = dms_to_decimal(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
        lon = dms_to_decimal(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))

        resolved = reverse_geocode(lat, lon)
        return {
            "status": "PHOTO_GEO_ACQUIRED",
            "lat": lat,
            "lon": lon,
            "resolved_address": resolved.get("display_name", "Unknown Landmark"),
            "summary": f"Photo geolocated to {resolved.get('display_name', '')} ({lat:.5f}, {lon:.5f})"
        }
    except Exception as e:
        return {"error": f"EXIF parsing error: {str(e)}"}
