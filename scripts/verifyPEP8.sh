#!/bin/bash

path_of_this_file=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
iu_path=$(dirname  $path_of_this_file)
make requirements
source .virtualenv/bin/activate
pep8 --exclude="Tests/integrationTests/repos/*",".git","bin","include","lib",\
"local" --statistics "$iu_path/API" "$iu_path/Exceptions" "$iu_path/GUI" \
"$iu_path/Model" "$iu_path/Parsers" "$iu_path/scripts" "$iu_path/Tests" \
"$iu_path/Validation"
