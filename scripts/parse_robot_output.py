# parse_robot_output.py
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
passed = failed = skipped = 0

for test in tests:
    status_elem = test.find("status")
    if status_elem is not None:
        status = status_elem.attrib.get("status", "")
        if status == "PASS":
            passed += 1
        elif status == "FAIL":
            failed += 1
        elif status == "SKIP":
            skipped += 1

percent = round((passed / total) * 100, 2) if total > 0 else 0

print(f"TOTAL={total}")
print(f"PASSED={passed}")
print(f"FAILED={failed}")
print(f"SKIPPED={skipped}")
print(f"PASS_PERCENT={percent}")
