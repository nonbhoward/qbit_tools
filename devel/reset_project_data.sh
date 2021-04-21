#!/bin/bash
clear
echo "deleting minimalog soft-link content"
rm -rf ./minimalog
echo "re-creating soft-link content from parallel directory"
ln -s ../minimalog ./minimalog
echo -e "finished soft-link operation, continuing.."
echo ""
git status
echo ""
if [ -f 'event.log' ];then
  echo 'removing event.log'
  rm event.log
else
  echo -e "event.log does not exist, continuing.."
fi
echo ""
echo 'restoring metadata_added.cfg'
git restore data_meta/metadata_added.cfg
echo 'restoring metadata_failed.cfg'
git restore data_meta/metadata_failed.cfg
echo 'restoring search.cfg'
git restore data_search/search.cfg
echo -e "finished restoring cfg files to repo versions, continuing.."
echo ""
if [ -f './devel/search.cfg' ];then
  echo 'developer search.cfg found'
  cp ./devel/search.cfg ./data_search/search.cfg
  echo 'attempted to overwrite project search.cfg with developer version'
else
  echo 'developer search.cfg not found'
  echo 'doing nothing'
fi
if [ -f './devel/EDIT_SETTINGS_HERE.cfg' ];then
  echo 'developer settings found'
  cp ./devel/EDIT_SETTINGS_HERE.cfg ./user_configuration/EDIT_SETTINGS_HERE.cfg
  echo 'attempted to overwrite project EDIT_SETTINGS_HERE.cfg with developer version'
else
  echo 'developer EDIT_SETTINGS_HERE.cfg not found'
  echo 'doing nothing'
fi
echo -e "finished overwriting local options with developer options, continuing.."
echo ""
git log --pretty=oneline -n8
echo ""
git status
