#!/bin/bash
clear
echo -e 'starting configuration restore routine..'
git status
echo -e '\trestoring metadata configurations!'
git restore ./data_meta/metadata_added.cfg
git restore ./data_meta/metadata_failed.cfg
echo -e '\trestoring search configurations!'
git restore ./data_search/search.cfg
echo -e '\trestoring user settings!'
git restore ./user_configuration/EDIT_SETTINGS_HERE.cfg
echo -e '\tdeleting event log!'
if [ -f event.log ]; then
	rm event.log
	echo -e '\tevent log removed!'
else
	echo -e '\tevent log not found!'
fi
git status
echo -e '\t..done!'
