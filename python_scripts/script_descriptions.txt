What the following do:

belcourt_extract.py

This takes the excel file generated from Agile and extracts just the titles, and the start and end dates. It also flags things separately if they mention seminars, rentals, etc.


set_35mm.py

This scans through a json file and analyzes if the title has "(35mm)" in it, it sets the 35mm column to true, if not false.


set_repertory.py

This file compares the year a film played to it's correlated IMDb film release year... if it's more than 4 years old, it marks that the film is a repertory film. If not, it's a new release.

set_venue.py

This file goes through and adds "Belcourt Theatre" as the venue/company to all entries that have played post-2000.

