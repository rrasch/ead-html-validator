#!/bin/bash

set -eu

EAD_DIR=$HOME/work/findingaids_eads_test

HTML_ROOT=$HOME/work/scratch/with-do-lookup/public

CMD="$HOME/work/ead-html-validator/ead-html-validator.py"

MPROF="mprof run --include-children"

NOW=$(date +'%Y-%m-%d')

CSV_FILE="validator_runtimes_${NOW}.csv"

readarray -d '' EAD_FILES < <(find "$EAD_DIR/" -name '*.xml' -print0 \
	| egrep -vz '(no-ns|pretty).xml$' | sort -z)

ARGS=("" "--multiprocessing" "--threading")

echo -n "partner,collection" > $CSV_FILE
echo -n ",duration no parallelization,exit code no parallelization" >> $CSV_FILE
echo -n ",duration multi-process,exit code multi-process" >> $CSV_FILE
echo -n ",duration multi-threads,exit code multi-threads" >> $CSV_FILE
echo >> $CSV_FILE

run()
{
	echo "Running command '$@'"
	set +e
	"$@"
	exit_code=$?
	set -e
	echo "exit_code=$exit_code"
}

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
		desc=${ARGS[$i]#--}
		desc=${desc:-single}
		data_file="mprofile_${partner}_${collection}_${desc}_${NOW}.dat"
		start_time=$(date +%s)
		run $CMD ${ARGS[$i]} "$@" "$file" "$html_dir"
		end_time=$(date +%s)
		duration=$((end_time - start_time))
		echo -n ",$duration,$exit_code" >> $CSV_FILE
	done
	echo >> $CSV_FILE
done

