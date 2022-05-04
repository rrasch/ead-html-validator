#!/usr/bin/env python

import csv
import re

libdir = "/home/rasan/work/ead_indexer/lib/ead_indexer"

files = [
    "behaviors.rb"
#     "document.rb",
#     "behaviors/component.rb",
#     "behaviors/dates.rb",
#     "behaviors/document.rb"
]

out = open('out.tsv', 'w', newline='')
writer = csv.writer(out, delimiter="\t")
writer.writerow(['Solr Field', 'EAD Field', 'Source'])
writer.writerow(['root', 'ead', 'document.rb'])
writer.writerow(['eadid', '', 'document.rb'])

for file in files:

    full_path = f"{libdir}/{file}"

    with open(full_path) as f:
        for line in f:
            line = line.strip()
            result = re.search(r'\s*t\.(\w+)\(path:"([^"]+)",index_as:', line)
            if result:
                name = result.group(1)
                xpath = result.group(2)
                writer.writerow([name, xpath, file])
    
            result = re.search(
                r'\s*Solrizer.(?:insert|set)_field\((?:fields|solr_doc), "([^"]+)",\s*([^\s]+)',
                line)
            if result:
                name = result.group(1)
                expr = result.group(2)
                writer.writerow([name, expr, file])

            result = re.search(
                r'\s*addl_fields\[Solrizer\.solr_name\("([^"]+)".*= (.*)$',
                line)
            if result:
                name = result.group(1)
                value = result.group(2)
                print(name)
                print(value)
                writer.writerow([name, value, file])
                


out.close()

