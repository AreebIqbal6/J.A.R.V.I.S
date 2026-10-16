"""
Backend/Sanitizer.py
Phase 5: Server-side markdown-to-HTML conversion and HTML sanitization
for the Dynamic Fallback Panel.
Allowed tags: <h3>, <h4>, <p>, <ul>, <ol>, <li>, <b>, <strong>, <i>, <em>, <code>, <pre>, <table>, <tr>, <th>, <td>, <br>, <span>, <div>.
Strictly strips: <script>, <iframe>, <object>, <embed>, <link>, <style>, on* handlers, and javascript: URIs.
"""

import re
import html

ALLOWED_TAGS = {
    "h3", "h4", "p", "ul", "ol", "li", "b", "strong",
    "i", "em", "code", "pre", "table", "thead", "tbody",
    "tr", "th", "td", "br", "span", "div", "hr",
    "button", "input", "label", "select", "option", "textarea", "meter", "progress"
}

SAFE_ATTRS = {"class", "id", "type", "value", "placeholder", "min", "max", "step", "title", "rows", "cols", "disabled", "readonly", "style"}

def sanitize_html(raw_html: str) -> str:
    """
    Sanitizes HTML string server-side.
    Strips scripts, iframes, styles, links, and dangerous event handlers.
    Ensures only allowlisted tags remain.
    """
    if not raw_html:
        return ""

    # 1. Strip dangerous tag blocks entirely
    clean = re.sub(r'<(script|iframe|object|embed|style|link|meta)\b[^<]*(?:(?!<\/\1>)<[^<]*)*<\/\1>', '', raw_html, flags=re.IGNORECASE)
    clean = re.sub(r'<(script|iframe|object|embed|style|link|meta)\b[^>]*\/?>', '', clean, flags=re.IGNORECASE)

    # 2. Strip event handlers (e.g. onclick="...", onload="...")
    clean = re.sub(r'\s+on[a-zA-Z]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', '', clean, flags=re.IGNORECASE)

    # 3. Strip javascript: URIs
    clean = re.sub(r'(href|src)\s*=\s*(?:"javascript:[^"]*"|\'javascript:[^\']*\'|javascript:[^\s>]+)', r'\1="#"', clean, flags=re.IGNORECASE)

    # 4. Filter tags to allowlist and retain safe attributes
    def tag_filter(match):
        full_tag = match.group(0)
        tag_name = match.group(1).lower()
        attr_str = match.group(2) if match.lastindex >= 2 else ""
        is_closing = full_tag.startswith("</")
        if tag_name in ALLOWED_TAGS:
            if is_closing:
                return f"</{tag_name}>"
            
            # Extract safe attributes
            safe_attrs_found = []
            if attr_str:
                for attr_match in re.finditer(r'([a-zA-Z0-9_\-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))', attr_str):
                    a_name = attr_match.group(1).lower()
                    a_val = attr_match.group(2) or attr_match.group(3) or attr_match.group(4) or ""
                    if a_name in SAFE_ATTRS or a_name.startswith("data-"):
                        if a_name == "style":
                            if "expression" in a_val.lower() or "url(" in a_val.lower():
                                continue
                        safe_attrs_found.append(f'{a_name}="{html.escape(a_val)}"')
            
            if safe_attrs_found:
                return f"<{tag_name} {' '.join(safe_attrs_found)}>"
            return f"<{tag_name}>"
        return ""

    clean = re.sub(r'<\/?([a-zA-Z0-9]+)([^>]*)>', tag_filter, clean)
    return clean.strip()

def markdown_to_safe_html(text: str) -> str:
    """
    Converts plain text or basic markdown from assistant responses
    into sanitized, clean HTML conforming to the allowlist.
    """
    if not text:
        return ""

    lines = [l.rstrip() for l in text.strip().split("\n")]
    html_parts = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        # Header 1-3
        header_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if header_match:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            header_text = html.escape(header_match.group(2))
            html_parts.append(f"<h3>{header_text}</h3>")
            continue

        # Bullet point or numbered list item
        list_match = re.match(r'^[-*•]\s+(.+)$', stripped) or re.match(r'^\d+\.\s+(.+)$', stripped)
        if list_match:
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            item_text = list_match.group(1)
            # Inline formatting
            item_text = _format_inline(item_text)
            html_parts.append(f"<li>{item_text}</li>")
            continue

        # Regular paragraph line
        if in_list:
            html_parts.append("</ul>")
            in_list = False

        para_text = _format_inline(stripped)
        html_parts.append(f"<p>{para_text}</p>")

    if in_list:
        html_parts.append("</ul>")

    raw_output = "".join(html_parts)
    return sanitize_html(raw_output)

def _format_inline(text: str) -> str:
    """Applies safe bold, italic, code formatting to plain text."""
    # Escape HTML first
    escaped = html.escape(text)
    # Bold **text** or __text__
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)
    escaped = re.sub(r'__(.+?)__', r'<b>\1</b>', escaped)
    # Italic *text* or _text_
    escaped = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', escaped)
    # Inline code `code`
    escaped = re.sub(r'`(.+?)`', r'<code>\1</code>', escaped)
    return escaped

def derive_dynamic_title(query: str, default: str = "DYNAMIC_QUERY_RESULT") -> str:
    """Derives a clean, uppercase HUD title from the query."""
    q = query.lower().strip()
    # Strip common conversational preambles
    q = re.sub(r'^(can you |please |tell me |explain |how do i |how to |what is |what are |who is |where is )', '', q).strip()
    q = re.sub(r'[?!.]+$', '', q).strip()
    if q:
        clean_words = q[:35].strip().upper()
        return f"INFO // {clean_words}"
    return f"[{default}]"

def prevent_ssti_and_injection(text: str, max_chars: int = 10000) -> str:
    """
    Guards against Server-Side Template Injection (SSTI), ReDoS, and malicious control characters.
    Truncates excessive payloads to prevent regex denial-of-service.
    """
    if not text:
        return ""
    # 1. Truncate payload length (ReDoS prevention)
    bounded = str(text)[:max_chars]
    
    # 2. Strip NULL bytes and dangerous non-printable control characters
    bounded = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', bounded)
    
    # 3. Defuse template delimiters (SSTI defense)
    bounded = bounded.replace("{{", "{ {").replace("}}", "} }")
    bounded = bounded.replace("{%", "{ %").replace("%}", "% }")
    bounded = bounded.replace("<%=", "< %=").replace("%>", "% >")
    
    return bounded

def sanitize_clipboard(text: str, max_chars: int = 2500) -> str:
    """
    Guards against clipboard payload injections and buffer overflow exploits.
    """
    if not text:
        return ""
    clean = prevent_ssti_and_injection(text, max_chars=max_chars)
    return clean.strip()

