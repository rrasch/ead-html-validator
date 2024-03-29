#!/bin/bash

set -u
set -e

if [ -d ~/venv/ead-html-validator ]; then
	source ~/venv/ead-html-validator/bin/activate
fi

export PYTHONUNBUFFERED=true

#./ead-html-validator.py -d Omega-EAD.xml ~/omega/guides/tamwag/mos_2021/ 2>&1 | tee out.log

VERBOSE=""

# for dtype in simple unified unified-color color
for dtype in color
do
	./ead-html-validator.py  $VERBOSE --diff-type $dtype "$@" \
		~/work/findingaids_eads_test/tamwag/mos_2021.xml \
		~/work/findingaids-hugo-public/tamwag/mos_2021 2>&1 | tee validator-$dtype.log
done

# zip logfiles.zip validator-*.log

