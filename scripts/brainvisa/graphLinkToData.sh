#!/bin/bash
# database rep en entree
if [ $# -lt 1 ]
then
  echo "Give the directory to parse in argument."
elif [ -d $1 ]
then
# get the abspath
rep=$(cd "$1" && pwd) 
# chercher les .arg
for graph in `find $rep -name "*.arg"`
do
  path=`dirname $graph`
  parent_path=`dirname $path`
  # chercher attribut filename_base qui donne le nom du .data
  line=`grep "filename_base" $graph`
  if [ -n "$line" ]
  then
    # recupere le nom du fichier
    data="${line##* }"
    if [ "$data" != "*" ]
    then
      # s'il n'existe pas dans le repertoire du graphe, et qu'il existe dans le rep parent, creer un lien vers ce .data dans le rep du graphe
      data_path=$path"/$data"
      data_parent_path=$parent_path"/"$data
      if [ ! -e $data_path ] && [ -e $data_parent_path ]
      then
        echo "Add a link $data_path -> $data_parent_path"
        ln -s $data_parent_path $data_path
      fi
    fi
  fi
done
else
  echo $1 " is not a directory."
fi
