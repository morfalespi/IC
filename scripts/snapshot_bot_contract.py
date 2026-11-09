"""Extract required result fields from the official Bot API HTML tables."""
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import sys

class Tables(HTMLParser):
    def __init__(self):
        super().__init__(); self.section = None; self.cell = None; self.row = []; self.rows = {}; self.heading = False
    def handle_starttag(self, tag, attrs):
        if tag == 'h4': self.heading = True; self.section = None
        if tag == 'a' and self.heading:
            name = dict(attrs).get('name')
            if name in {'user','chat','chatfullinfo','acceptedgifttypes','message','file'}: self.section = name; self.rows.setdefault(name, [])
        if tag == 'tr': self.row = []
        if tag == 'td': self.cell = ''
    def handle_data(self, text):
        if self.cell is not None: self.cell += text
    def handle_endtag(self, tag):
        if tag == 'h4': self.heading = False
        if tag == 'td' and self.cell is not None:
            self.row.append(' '.join(self.cell.split())); self.cell = None
        if tag == 'tr' and self.section and len(self.row) == 3:
            self.rows[self.section].append(self.row)

raw = Path(sys.argv[1]).read_bytes()
p = Tables(); p.feed(raw.decode())
contract = {'source':'https://core.telegram.org/bots/api','source_sha256':hashlib.sha256(raw).hexdigest(), 'scope':'Required top-level fields only; not the entire Bot API schema', 'types':{name:{field:kind for field,kind,description in rows if not description.startswith('Optional')} for name,rows in p.rows.items()}}
assert set(contract['types']) == {'user','chat','chatfullinfo','acceptedgifttypes','message','file'}
Path('tests/contracts/bot-api-required.json').write_text(json.dumps(contract,indent=2)+'\n')
print(json.dumps(contract,indent=2))
