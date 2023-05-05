# banking-status

## Overview
Until all of this data is in Looker it's a bit of a manual process to generate and analyze the data.  This describes the process that must be undertaken, for now.

## Set up your environment
1. Clone this repo
2. Create a Python virtual environment (IntelliJ will even do this for you)

As of this writing no additional pip packages are required but maybe that will change in the future, so it's best to use a virtual environment.

## Pull down the latest data
1. Pull latest Ecomm opportunity data from [this Look](https://toasttab.looker.com/looks/11009)
   1. Download via the Gear icon > `Download`
   1. Format: CSV
   1. Filename: Prospect-Buys-with-GUIDs (Looker will auto-append `.csv`)
   1. Results: As displayed in the data table
   1. Data values: Unformatted
   1. Number of rows and columns to include: All results
   1. Remove all sorts from query: Unchecked
   1. Drop results into `data/Prospect-Buys-with-GUIDs.csv`
1. Pull latest booked to workable timing from Snowflake
   1. Snowflake query to run is in `data/queries/snowflake/booked-to-workable-timing`
   1. Drop results into `data/booked-to-workable-timing.csv`
1. Pull latest provide-location-banking-info task data from Snowflake
   1. Snowflake query to run is in `data/queries/snowflake/provide-location-banking-info--most-recent-revision`
   1. Drop results into `data/provide-location-banking-info--most-recent-revision.csv`
1. Pull latest self-service-leave-test-mode task data from Snowflake
   1. Snowflake query to run is in `data/queries/snowflake/self-service-leave-test-mode--most-recent-revision`
   1. Drop results into `data/self-service-leave-test-mode--most-recent-revision.csv`
1. Pull latest GIACT pass/fail event data from Splunk
   1. Splunk query to run is in `data/queries/splunk/giact-results-non-deduped`
   1. GIACT was introduced in November 2022 so set the date range to ~11/01/2022 to present. You may want to break it into chunks of files since the larger the date range, the more likely Splunk is to fail.
   1. Drop results into the relevant file names (see script).

## Run the script
1. Run `./script.py`
   1. You may need to `chmod +x script.py`
1. `results.csv` is generated, along with some other info written to the console

## Load the results into Google Sheets
1. Clone [this sheet](https://docs.google.com/spreadsheets/d/1w6bIW2Y6dcwboHdNVA7C6c0Wjh0pY3jLgKyqPyhFmVY/edit#gid=1390792315)
1. Choose tab `Current #s (raw data)`
1. `File > Import > Upload`
   1. Select `results.csv`
1. Choose `Replace current sheet` and uncheck `Convert text to numbers, dates, and formulas`
   1. If you do not uncheck that box, some weird things happen like GUIDs being converted to numbers in scientific notation
   1. Because this box is unchecked, the step below needs to be followed, otherwise the formulas won't work
1. Change the format of a couple columns. 
   1. Click column B and select `Format > Number > Date`
      1. Column B: Opportunities Opportunity Created Date
   1. Click column L and select `Format > Number > Number`
      1. Column L: Booked to Workable Days 
1. The data in tab `Current #s (analysis)` should be automatically updated

## Troubleshooting
1. If the script fails
   1. Ensure the file names for the input data are accurate 
   1. Ensure all column headers in the source files are accurate (see `script.py` for expected column names) and in the correct order
1. If Google Sheets is being weird
   1. Ensure the named ranges are in place `Data > Named ranges`
   1. Ensure you changed the format of the specified columns (see above) after importing the data
   1. Ensure there are no blank rows at the bottom of the source sheet.
