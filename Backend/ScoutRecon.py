"""
Backend/ScoutRecon.py
Scout Web Intelligence & Lead Reconnaissance Engine
Inspired by kiryano/Scout (https://github.com/kiryano/Scout) and firecrawl/open-scouts.
Provides automated profile, domain, and company OSINT reconnaissance with structured lead scoring.
"""

import re
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List

logger = logging.getLogger("JARVIS_Scout")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}')

KNOWN_TECH_SIGNATURES = {
    "Cloudflare": ["cloudflare", "cf-ray"],
    "Next.js": ["_next", "__NEXT_DATA__"],
    "React": ["react", "react-dom"],
    "Vue.js": ["vue", "v-cloak"],
    "WordPress": ["wp-content", "wp-includes"],
    "Shopify": ["cdn.shopify.com", "shopify"],
    "Stripe": ["js.stripe.com", "stripe"],
    "Tailwind CSS": ["tailwind"]
}

def scout_target_domain(domain_or_url: str) -> Dict[str, Any]:
    """
    Performs deep OSINT reconnaissance on a target company or domain.
    Extracts emails, phone numbers, social links, technologies, and metadata.
    """
    target = domain_or_url.strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        target_url = f"https://{target}"
    else:
        target_url = target

    headers = {"User-Agent": USER_AGENT}

    try:
        res = requests.get(target_url, headers=headers, timeout=6.0, verify=False)
        html = res.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Page Title & Meta
        title = soup.title.string.strip() if soup.title and soup.title.string else target
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()

        # 2. Extract Contact Info
        raw_emails = list(set(EMAIL_REGEX.findall(html)))
        # Filter out common false positives (like image extensions or font files)
        valid_emails = [e for e in raw_emails if not e.endswith(('.png', '.jpg', '.svg', '.webp', '.js', '.css', '.woff'))][:6]

        raw_phones = list(set(PHONE_REGEX.findall(html)))
        valid_phones = [p for p in raw_phones if len(re.sub(r'\D', '', p)) >= 10][:4]

        # 3. Social Media Links
        socials = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if "linkedin.com/company" in href or "linkedin.com/in" in href:
                socials["linkedin"] = a["href"]
            elif "github.com/" in href and not "github.com/login" in href:
                socials["github"] = a["href"]
            elif "twitter.com/" in href or "x.com/" in href:
                socials["twitter"] = a["href"]
            elif "instagram.com/" in href:
                socials["instagram"] = a["href"]
            elif "youtube.com/" in href:
                socials["youtube"] = a["href"]

        # 4. Tech Stack Signatures
        detected_tech = []
        html_lower = html.lower()
        for tech, sigs in KNOWN_TECH_SIGNATURES.items():
            if any(sig in html_lower for sig in sigs):
                detected_tech.append(tech)

        # 5. Lead Score Calculation
        score = 40
        if valid_emails: score += 25
        if valid_phones: score += 15
        if socials: score += 15
        if meta_desc: score += 5
        lead_score = min(100, score)

        return {
            "status": "RECON_COMPLETE",
            "target": target,
            "url": target_url,
            "title": title,
            "description": meta_desc,
            "emails": valid_emails,
            "phones": valid_phones,
            "social_links": socials,
            "technologies": detected_tech,
            "lead_score": f"{lead_score}%",
            "summary": f"Scout Recon for '{target}': {len(valid_emails)} email(s) detected. Tech: {', '.join(detected_tech) or 'Proprietary'}. Lead quality score: {lead_score}%."
        }

    except Exception as e:
        logger.error(f"Scout recon error for {domain_or_url}: {e}")
        return {"error": f"Reconnaissance failed for {domain_or_url}: {str(e)}"}
