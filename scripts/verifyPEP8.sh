path_of_this_file=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
iu_path=$(dirname  $path_of_this_file)
pep8 --statistics -qq $iu_path
