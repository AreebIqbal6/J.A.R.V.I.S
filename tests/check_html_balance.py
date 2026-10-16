from html.parser import HTMLParser

class TagBalanceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in self.void_tags:
            line, col = self.getpos()
            attr_dict = dict(attrs)
            tag_id = attr_dict.get('id', '')
            tag_class = attr_dict.get('class', '')
            self.stack.append((tag.lower(), line, tag_id, tag_class))

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.void_tags:
            return
        if not self.stack:
            line, col = self.getpos()
            self.errors.append(f"Line {line}: Unexpected closing </{tag_lower}> with empty stack")
            return
        
        last_tag, last_line, last_id, last_class = self.stack[-1]
        if last_tag == tag_lower:
            self.stack.pop()
        else:
            # Look backwards in stack to see if matched
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag_lower:
                    # Found matching tag higher up, meaning intermediate tags were unclosed!
                    line, col = self.getpos()
                    unclosed = self.stack[i+1:]
                    for u in unclosed:
                        self.errors.append(f"Unclosed <{u[0]}> (opened at line {u[1]}, id='{u[2]}', class='{u[3]}') before </{tag_lower}> at line {line}")
                    self.stack = self.stack[:i]
                    return
            line, col = self.getpos()
            self.errors.append(f"Line {line}: Mismatched closing </{tag_lower}> (expected </{last_tag}> from line {last_line} id='{last_id}')")

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    html = f.read()

parser = TagBalanceParser()
parser.feed(html)

print("=== TAG BALANCE CHECK ON jarvis_ui.html ===")
print(f"Total errors/unclosed tags found: {len(parser.errors)}")
for err in parser.errors[:25]:
    print("  [ERROR] ", err)

if parser.stack:
    print(f"\nTags left unclosed at EOF ({len(parser.stack)}):")
    for u in parser.stack[-15:]:
        print(f"  Unclosed <{u[0]}> from line {u[1]} id='{u[2]}' class='{u[3]}'")

