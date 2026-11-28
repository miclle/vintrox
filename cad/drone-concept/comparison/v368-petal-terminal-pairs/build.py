import hashlib
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile

base, source, output = map(Path, sys.argv[1:])
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if digest(base) != '2372bc6788487af2dc3de7e49eb6b34dfdfe7b835b523e0e44e9f466c948308b' or digest(source) != 'e3a70236111a729d6ad7d1ef48c4661e0145975bedefb72aa6d28df2f65b4a28':
    raise ValueError('Expected v363 and v339 saved models')
parts = {}
with ZipFile(source) as donor, ZipFile(base) as original, ZipFile(output, 'x') as result:
    for info in original.infolist():
        name = info.filename
        data = original.read(name)
        match = re.fullmatch(r'(NozzlePetal(?:EdgeRail|EndHem|Inset|Ridge|Hinge|Guide)?(\d+)(?:_\d+)?)\.Shape\.(brp|Map\.txt)', name)
        if match and int(match[2]) in {0, 4, 5, 11}:
            replacement = donor.read(name)
            if data != replacement:
                parts[name] = hashlib.sha256(replacement).hexdigest()
                data = replacement
        result.writestr(info, data)
print(json.dumps(parts, indent=2))
