"""
Backend/IPTV.py
Live Tactical IPTV & Media Monitor Engine
Integrated with iptv-org open directory (https://iptv-org.github.io/iptv/index.m3u)
Delivers live broadcast intelligence and space/news video streams directly to J.A.R.V.I.S.
"""

import requests
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("JARVIS_IPTV")

CURATED_CHANNELS = [
    {
        "id": "nasa",
        "name": "NASA TV — Orbital Stream",
        "category": "Science & Space",
        "country": "US",
        "url": "https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8",
        "badge": "ORBITAL // 408 KM",
        "desc": "Live video from the International Space Station, launch feeds, and deep space exploration."
    },
    {
        "id": "skynews",
        "name": "Sky News Live",
        "category": "World News",
        "country": "UK",
        "url": "https://skynewsau-live.akamaized.net/hls/live/2002689/skynewsau-extra1/master.m3u8",
        "badge": "NEWS // BREAKING",
        "desc": "Real-time 24/7 breaking international news broadcasts and geopolitical coverage."
    },
    {
        "id": "aljazeera",
        "name": "Al Jazeera English",
        "category": "World News",
        "country": "QA",
        "url": "https://live-hls-web-aje.getaj.net/AJE/01.m3u8",
        "badge": "GLOBAL DESK",
        "desc": "In-depth investigative reports, Middle East updates, and global affairs."
    },
    {
        "id": "euronews",
        "name": "Euronews English",
        "category": "European News",
        "country": "EU",
        "url": "https://euronews-euronews-world-1-au.samsung.wurl.tv/playlist.m3u8",
        "badge": "EU INTELLIGENCE",
        "desc": "European business, politics, science, and international headlines."
    },
    {
        "id": "weathernation",
        "name": "WeatherNation Live",
        "category": "Meteorology",
        "country": "US",
        "url": "https://weathernation.akamaized.net/hls/live/2034960/weathernation/master.m3u8",
        "badge": "METEOROLOGY",
        "desc": "Live radar mapping, extreme storm tracking, and global weather systems."
    },
    {
        "id": "dw",
        "name": "DW News (Deutsche Welle)",
        "category": "World News",
        "country": "DE",
        "url": "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8",
        "badge": "GLOBAL INTEL",
        "desc": "German international news and technology analysis broadcast."
    },
    {
        "id": "redbull",
        "name": "Red Bull TV",
        "category": "Extreme Tech & Sport",
        "country": "AT",
        "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8",
        "badge": "TACTICAL ACTION",
        "desc": "High-altitude aviation, motorsport engineering, and extreme athletic telemetry."
    }
]

def get_iptv_channels(category: Optional[str] = None) -> List[Dict]:
    """Returns curated active IPTV channels, optionally filtered by category."""
    if not category:
        return CURATED_CHANNELS
    cat_lower = category.lower()
    return [c for c in CURATED_CHANNELS if cat_lower in c["category"].lower()]

def get_channel_by_id(channel_id: str) -> Optional[Dict]:
    """Finds channel by ID."""
    cid = channel_id.lower().strip()
    for ch in CURATED_CHANNELS:
        if ch["id"] == cid or cid in ch["name"].lower():
            return ch
    return None

def verify_channel_stream(url: str, timeout: float = 3.0) -> bool:
    """Performs lightweight check to verify m3u8 stream availability."""
    try:
        r = requests.head(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return r.status_code in [200, 301, 302]
    except Exception:
        return False
