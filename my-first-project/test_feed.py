import urllib.request
import xml.etree.ElementTree as ET

url = "https://docs.cloud.google.com/feeds/bigquery-release-notes.xml"
try:
    print("Fetching feed...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
    print("Fetched successfully. Length:", len(xml_data))
    
    # Parse XML
    root = ET.fromstring(xml_data)
    print("Root tag:", root.tag)
    
    # Print namespaces
    # Standard atom feeds look like: {http://www.w3.org/2005/Atom}feed
    print("Root attributes:", root.attrib)
    
    # Print some child tags
    for child in list(root)[:15]:
        print("Child:", child.tag, child.attrib)
        if 'entry' in child.tag or 'item' in child.tag:
            for sub in child[:5]:
                print("  Sub-child:", sub.tag, sub.text[:100] if sub.text else '')
except Exception as e:
    print("Error:", e)
