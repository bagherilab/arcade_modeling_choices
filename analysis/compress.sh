#!/bin/bash

# List of JSON file extensions (comment out to ignore).
JSONS=(
    ".SEEDS.COUNTS"
    ".SEEDS.VOLUMES"
    ".SEEDS.DIAMETERS"
    ".SEEDS.STATES"
    ".SEEDS.GROWTH"
    ".SEEDS.SYMMETRY"
    ".SEEDS.CYCLES"
    ".SEEDS.ACTIVITY"
    ".METRICS.COUNTS"
    ".METRICS.VOLUMES"
    ".METRICS.DIAMETERS"
    ".METRICS.STATES"
    ".METRICS.GROWTH"
    ".METRICS.SYMMETRY"
    ".METRICS.CYCLES"
    ".METRICS.ACTIVITY"
    ".CONCENTRATIONS"
    ".CENTERS"
)

# List of CSV file extensions (comment out to ignore).
CSVS=(
    ".DISTRIBUTION"
    ".LOCATIONS"
    ".OUTLINES"
)

# Do nothing if no argument is passed.
if [[ $# -eq 0 ]] ; then
    exit 0
fi

# Compress all files for given simulation set name.
if [[ $# -eq 1 ]] ; then
    NAME=$1

    # Iterate through all JSON files to compress.
    for JSON in ${JSONS[@]}; do
        JSON_DIRECTORY=$NAME/_$NAME${JSON}
        JSON_TAR=$NAME${JSON}.tar.xz

        if [[ -d "$JSON_DIRECTORY" ]]
        then
            echo "$JSON_DIRECTORY already exists. Please move contents out and remove."
            continue
        fi

        if [[ -f "$NAME/$JSON_TAR" ]]
        then
            echo "$JSON_TAR already exists. Please remove."
            continue
        fi

        mkdir $JSON_DIRECTORY
        mv $NAME/$NAME\_*${JSON}.json $JSON_DIRECTORY
        cd $JSON_DIRECTORY
        COPYFILE_DISABLE=1 tar cJvf ../${JSON_TAR} *.json
        cd ../..
    done

    # Iterate through all CSV files to compress.
    for CSV in ${CSVS[@]}; do
        CSV_DIRECTORY=$NAME/_$NAME${CSV}
        CSV_TAR=$NAME${CSV}.tar.xz

        if [[ -d "$CSV_DIRECTORY" ]]
        then
            echo "$CSV_DIRECTORY already exists. Please move contents out and remove."
            continue
        fi

        if [[ -f "$NAME/$CSV_TAR" ]]
        then
            echo "$CSV_TAR already exists. Please remove."
            continue
        fi

        mkdir $CSV_DIRECTORY
        mv $NAME/$NAME\_*${CSV}*.csv $CSV_DIRECTORY
        cd $CSV_DIRECTORY
        COPYFILE_DISABLE=1 tar cJvf ../${CSV_TAR} *.csv
        cd ../..
    done
fi

# Compress all files for given simulation set name.
if [[ $# -eq 3 ]] ; then
    NAME=$1
    EXT=$2
    TYPE=$3

    DIRECTORY=$NAME/_$NAME$EXT
    TAR=$NAME$EXT.tar.xz

    if [[ -d "$DIRECTORY" ]]
    then
        echo "$DIRECTORY already exists. Please move contents out and remove."
        exit 0
    fi

    if [[ -f "$NAME/$TAR" ]]
    then
        echo "$TAR already exists. Please remove."
       exit 0
    fi

    mkdir $DIRECTORY
    mv $NAME/$NAME\_*${EXT}*.${TYPE} $DIRECTORY
    cd $DIRECTORY
    COPYFILE_DISABLE=1 tar cJvf ../${TAR} *.${TYPE}
    cd ../..
fi