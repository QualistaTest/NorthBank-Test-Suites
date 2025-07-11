import xml.etree.ElementTree as ET
import sys
import os

path = sys.argv[1] if len(sys.argv) > 1 else "results/output.xml"

if not os.path.exists(path):
    print("TOTAL=0\nPASSED=0\nFAILED=0\nSKIPPED=0\nPASS_PERCENT=0")
    sys.exit(0)

tree = ET.parse(path)
tests = tree.findall(".//test")

total = len(tests)
passed = sum(1 for t in tests if t.attrib.get('status') == 'PASS')
failed = sum(1 for t in tests if t.attrib.get('status') == 'FAIL')
skipped = sum(1 for t in tests if t.attrib.get('status') == 'SKIP')

if total == 0:
    percent = 0
else:
    percent = round((passed / total) * 100, 2)

print(f"TOTAL={total}")
print(f"PASSED={passed}")
print(f"FAILED={failed}")
print(f"SKIPPED={skipped}")
print(f"PASS_PERCENT={percent}")
