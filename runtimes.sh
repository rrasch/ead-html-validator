#!/bin/bash

set -u

EAD_DIR=$HOME/work/findingaids_eads_test

HTML_ROOT=$HOME/work/scratch/with-do-lookup/public

CMD="$HOME/work/ead-html-validator/ead-html-validator.py"

CSV_FILE="validator_runtimes_$(date +'%Y-%m-%d').csv"

readarray -d '' EAD_FILES < <(find "$EAD_DIR" -name '*.xml' -print0 \
	| egrep -vz '(no-ns|pretty).xml$')

ARGS=("" "--multiprocessing" "--threading")

echo "partner,collection" > $CSV_FILE
echo -n ",duration no parallelization" >> $CSV_FILE
echo -n ",duration multi-process" >> $CSV_FILE
echo -n ",duration multi-threads" >> $CSV_FILE

for file in "${EAD_FILES[@]}"
do
	tmp=${file#"$EAD_DIR"}
	tmp=${tmp#/}
	tmp=${tmp%.xml}
	partner=${tmp%%/*}
	collection=${tmp#*/}
	html_dir="$HTML_ROOT/$partner/$collection/"
	index_file="${html_dir}index.html"
	if [ ! -f "$index_file" ]; then
		echo "$index_file doesn't exist. Skipping $partner/$collection ..."
		continue
	fi
	echo -n "$partner,$collection" >> $CSV_FILE
	for i in "${!ARGS[@]}"
	do
		start_time=$(date +%s)
		set +e
		$CMD ${ARGS[$i]} "$file" "$html_dir"
		set -e
		end_time=$(date +%s)
		duration=$((end_time - start_time))
		echo -n ",$duration" >> $CSV_FILE
	done
	echo >> $CSV_FILE
done

