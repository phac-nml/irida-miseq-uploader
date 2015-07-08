#!/bin/bash

path_of_this_file=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
iu_path=$(dirname  $path_of_this_file)
echo iu_path
pep8 --exclude="Tests/integrationTests/repos/*",".git" --statistics .
