#!/usr/bin/env python3

import csv
from datetime import datetime

# if giact both passed and failed for a GUID
giactPassAndFail = set()

# giact passed but no COMPLETED in banking task status
giactPassedButBankingTaskNotCompleted = {}

# go-live task is COMPLETED but booked to workable days is less than zero
liveButBookedToWorkableMissing = {}

# reached workable (stage 16) but banking task is incomplete
workableButBankingIncomplete = {}


def bankingStatusFromTaskStatuses(taskStatusesSet):
    # TODO: What to do about 'CANCELED'
    # This function was originally meant to ascertain a status based on
    # the aggregate of all task statuses encountered.
    # The input data has since been scrubbed to only show most recent task status,
    # but this code is being maintained to support the scenario where
    # all historic task statuses are passed.
    if 'COMPLETED' in taskStatusesSet:
        return 'Completed'
    if 'ON_HOLD' in taskStatusesSet:
        return 'On hold'
    if 'IN_PROGRESS' in taskStatusesSet:
        return 'In progress'
    if 'NEW' in taskStatusesSet:
        return 'Not started'
    return 'Unknown'


def checkForAnomalies(row):
    if row['Passed Auto GIACT'] == 'Yes' and row['Failed Auto GIACT'] == 'Yes':
        giactPassAndFail.add(row['Customer Account Toast Guid'])

    taskStatusesSet = set(row['Banking Task Statuses'].split(','))
    if row['Passed Auto GIACT'] == 'Yes' and 'COMPLETED' not in taskStatusesSet:
        giactPassedButBankingTaskNotCompleted[row['Customer Account Toast Guid']] = row['Banking Task Statuses']

    if row['Go Live Status'] == 'COMPLETED' and int(row['Booked to Workable Days']) < 0:
        liveButBookedToWorkableMissing[row['Customer Account Toast Guid']] = row['Booked to Workable Days']

    if int(row['Booked to Workable Days']) >= 0 and row['Banking Status'] != 'Completed':
        oppDate = row['Opportunities Opportunity Created Date']
        oppDate = datetime.strptime(oppDate, "%m/%d/%Y")
        if oppDate.date() >= datetime.strptime("11/24/2022", "%m/%d/%Y").date():
            workableButBankingIncomplete[row['Customer Account Toast Guid']] = row['Booked to Workable Days']


ecommOpps = 'data/Prospect-Buys-with-GUIDs.csv'
bankingTaskStatusFile = 'data/provide-location-banking-info--most-recent-revision.csv'  # run data/queries/snowflake/provide-location-banking-info--most-recent-revision and export to CSV
goliveTaskStatusFile = 'data/self-service-leave-test-mode--most-recent-revision.csv'  # run data/queries/snowflake/self-service-leave-test-mode--most-recent-revision and export to CSV
giactResultsFiles = ['data/giact-nov22-apr23.csv',
                     'data/giact-since-may.csv']  # run data/queries/splunk/giact-results-non-deduped and export to CSV(s)
bookedToWorkableResultsFile = 'data/booked-to-workable-timing.csv'  # run data/queries/booked-to-workable-timing and export to CSV

rxToBankingStatus = {}
rxToLiveStatus = {}
rxToGiactResults = {}
rxToBookedToWorkableDays = {}

# create a mapping of Rx GUID to all Task Statuses it has experienced
# task statuses (if more than one) are lexicographically sorted, i.e. not sorted by order of occurrence
with open(bankingTaskStatusFile, mode='r') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        rxToBankingStatus[row['RESTAURANTID']] = row['STATUSES']

# create a mapping of Rx GUID to current go-live status
with open(goliveTaskStatusFile, mode='r') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        rxToLiveStatus[row['RESTAURANTID']] = row['STATUSES']

# create a mapping of Rx GUID to giact pass and/or fail events
for giactResultsFile in giactResultsFiles:
    with open(giactResultsFile, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            # res == 'pass' or 'fail'
            if row['merchantId'] not in rxToGiactResults.keys():
                rxToGiactResults[row['merchantId']] = set()
            rxToGiactResults[row['merchantId']].add(row['res'])

# create a mapping of Rx GUID to booked-to-workable timing in days
with open(bookedToWorkableResultsFile, mode='r') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        rxToBookedToWorkableDays[row['RESTAURANTID']] = row['BOOKED_TO_WORKABLE_DAYS']

results = "results.csv"
writerFieldNames = ['Customer Account Name',
                    'Opportunities Opportunity Created Date',
                    'Accounts Salesforce Account ID',
                    'Customer Account Toast Guid',
                    'Passed Auto GIACT',
                    'Failed Auto GIACT',
                    'Banking Status',
                    'Banking Task Statuses',
                    'Go Live Status',
                    'Booked to Workable Days'
                    ]

with open(ecommOpps, mode='r') as infile, open(results, "w") as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=writerFieldNames, extrasaction='ignore')
    writer.writeheader()
    for row in reader:
        # add new rows
        row['Passed Auto GIACT'] = ""
        row['Failed Auto GIACT'] = ""
        row['Banking Status'] = ""
        row['Banking Task Statuses'] = ""
        row['Go Live Status'] = ""
        row['Booked to Workable Days'] = ""

        # convert opportunity creation date to google sheets friendly format
        oppDate = datetime.strptime(row['Opportunities Opportunity Created Date'], "%Y-%m-%d").strftime("%m/%d/%Y")
        row['Opportunities Opportunity Created Date'] = oppDate

        rxGuid = row['Customer Account Toast Guid']

        # populate giact pass and giact fail columns
        if rxGuid in rxToGiactResults:
            if 'pass' in rxToGiactResults[rxGuid]:
                row['Passed Auto GIACT'] = 'Yes'
            if 'fail' in rxToGiactResults[rxGuid]:
                row['Failed Auto GIACT'] = 'Yes'

        # populate banking status column
        # populate customer-task-service values column
        if rxGuid in rxToBankingStatus:
            bankingStatus = rxToBankingStatus[rxGuid]
            bankingStatusSet = set(bankingStatus.split(','))
            row['Banking Status'] = bankingStatusFromTaskStatuses(bankingStatusSet)
            row['Banking Task Statuses'] = rxToBankingStatus[rxGuid]

        # populate go live status column
        if rxGuid in rxToLiveStatus:
            row['Go Live Status'] = rxToLiveStatus[rxGuid]
            # If the go-live status is completed, set "Banking Status" to Completed
            # If they're live, they must have banking in place
            if row['Go Live Status'] == 'COMPLETED':
                tempSet = set()
                tempSet.add('COMPLETED')
                row['Banking Status'] = bankingStatusFromTaskStatuses(tempSet)

        # populate booked to workable days column
        if rxGuid in rxToBookedToWorkableDays:
            row['Booked to Workable Days'] = rxToBookedToWorkableDays[rxGuid]
        else:
            row['Booked to Workable Days'] = -1

        checkForAnomalies(row)
        writer.writerow(row)

# print anomalies
print("GIACT PASS AND FAIL\n---")
print(giactPassAndFail, "\n")

print("GIACT PASS BUT BANKING TASK NOT COMPLETED\n---")
print(giactPassedButBankingTaskNotCompleted, "\n")

print("LIVE BUT BOOKED TO WORKABLE MISSING\n---")
print(liveButBookedToWorkableMissing, "\n")

print("WORKABLE BUT BANKING INCOMPLETE (11/24/2022 and on)\n---")
if len(workableButBankingIncomplete) > 20:
    print(f"entries: {len(workableButBankingIncomplete)}")
else:
    print(workableButBankingIncomplete)
print("\n")
