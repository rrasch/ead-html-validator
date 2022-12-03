#!/bin/bash

set -u
set -e

export PYTHONUNBUFFERED=true

#./ead-html-validator.py -d Omega-EAD.xml ~/omega/guides/tamwag/mos_2021/ 2>&1 | tee out.log

# for dtype in simple unified unified-color color
for dtype in color
do
	./ead-html-validator.py --diff-type $dtype Omega-EAD.xml \
		~/work/findingaids-hugo-public/tamwag/mos_2021 2>&1 | tee validator-$dtype.log
done

zip logfiles.zip validator-*.log

