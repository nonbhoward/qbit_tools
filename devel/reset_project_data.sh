#!/bin/bash
clear
echo "deleting minimalog soft-link content"
rm -rf ./minimalog
echo "re-creating soft-link content from parallel directory"
ln -s ../minimalog ./minimalog
echo "operation finished"
git status
if [ -f 'event.log' ]
then
  echo 'removing event.log'
  rm event.log
else
  echo 'event.log does not exist, continuing..'
fi
echo 'restoring metadata_added.cfg'
git restore data_meta/metadata_added.cfg
echo 'restoring metadata_failed.cfg'
git restore data_meta/metadata_failed.cfg
echo 'restoring search.cfg'
git restore data_search/search.cfg
git log --pretty=oneline -n8
git status
