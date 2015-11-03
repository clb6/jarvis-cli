#!/bin/bash
#
# Purpose of this script is to enforce consistency and for convenience. Every log
# entry should have some basic information: author, created timestamp, file
# format version, and tags. This script creates a new a file with those critical
# components.
#

# TODO: These should part of the shell env rather than here. This would require
# some installation script but let's see how far this project gets.
PIM_ENV_DIR_LOGS="$HOME/oz/Documents/Dump/LogEntries"
PIM_ENV_AUTHOR="Michael Hwang"
# Using SemVer because I can't think of a reason for why not.
PIM_ENV_VERSION="0.1.0"

ENTRY_FILENAME="$PIM_ENV_DIR_LOGS/$(date +%s).md"

echo "Author: $PIM_ENV_AUTHOR" >> $ENTRY_FILENAME
echo "Created: $(date -u --iso-8601=second)" >> $ENTRY_FILENAME
echo "Version: $PIM_ENV_VERSION" >> $ENTRY_FILENAME
echo "Tags: " >> $ENTRY_FILENAME

vim $ENTRY_FILENAME
