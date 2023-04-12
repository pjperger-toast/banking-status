#!/usr/bin/env python3

import csv

# if giact both passed and failed for a GUID
giactPassAndFail = set()

# giact passed but no COMPLETED in task statuses
giactPassedButTaskNotCompleted = {}


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
    if row['Passed Auto GIACT'] == 'True' and row['Failed Auto GIACT'] == 'True':
        giactPassAndFail.add(row['Customer Account Toast Guid'])

    taskStatusesSet = set(row['Banking Task Statuses'].split(','))
    if row['Passed Auto GIACT'] == 'True' and 'COMPLETED' not in taskStatusesSet:
        giactPassedButTaskNotCompleted[row['Customer Account Toast Guid']] = row['Banking Task Statuses']


inputFile = 'AlleCommProspectAccountsWithGUIDS - explore_gtm all_opps 2023-04-11T1016.csv'
bankingTaskStatusFile = 'provide-location-banking-info most recent revision.csv'  # run query in snowflake-query and export to CSV
giactResultsFile = 'giact-results-ytd-2-non-deduped.csv'  # run query in splunk-query and export to CSV

rxToBankingStatus = {}
rxToGiactResults = {}

# create a mapping of Rx GUID to all Task Statuses it has experienced
# task statuses are lexicographically sorted, i.e. not sorted by order of occurrence
with open(bankingTaskStatusFile, mode='r') as infile:
    reader = csv.DictReader(infile)
    next(reader)
    for row in reader:
        rxToBankingStatus[row['RESTAURANTID']] = row['STATUSES']

# create a mapping of Rx GUID to giact pass and/or fail events
with open(giactResultsFile, mode='r') as infile:
    reader = csv.DictReader(infile)
    next(reader)
    for row in reader:
        # res == 'pass' or 'fail'
        if row['merchantId'] not in rxToGiactResults.keys():
            rxToGiactResults[row['merchantId']] = set()
        rxToGiactResults[row['merchantId']].add(row['res'])

results = "results.csv"
writerFieldNames = ['Customer Account Name',
                    'Opportunities Opportunity Created Date',
                    'Accounts Salesforce Account ID',
                    'Customer Account Toast Guid',
                    'Opportunities Total Software ARR',
                    'Opportunity Line Item Hardware Value',
                    'Passed Auto GIACT',
                    'Failed Auto GIACT',
                    'Banking Status',
                    'Banking Task Statuses'
                    ]

with open(inputFile, mode='r') as infile, open(results, "w") as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=writerFieldNames)
    _ = next(reader)
    writer.writeheader()
    for row in reader:
        # add new rows
        row['Passed Auto GIACT'] = ""
        row['Failed Auto GIACT'] = ""
        row['Banking Status'] = ""
        row['Banking Task Statuses'] = ""

        cxGuid = row['Customer Account Toast Guid']

        # populate giact pass and giact fail columns
        if cxGuid in rxToGiactResults:
            if 'pass' in rxToGiactResults[cxGuid]:
                row['Passed Auto GIACT'] = 'True'
            if 'fail' in rxToGiactResults[cxGuid]:
                row['Failed Auto GIACT'] = 'True'

        # populate banking status column
        # populate customer-task-service values column
        if cxGuid in rxToBankingStatus:
            bankingStatus = rxToBankingStatus[cxGuid]
            bankingStatusSet = set(bankingStatus.split(','))
            row['Banking Status'] = bankingStatusFromTaskStatuses(bankingStatusSet)
            row['Banking Task Statuses'] = rxToBankingStatus[cxGuid]

        checkForAnomalies(row)
        writer.writerow(row)

# print anomalies
print("GIACT PASS AND FAIL\n---")
print(giactPassAndFail, "\n")

print("GIACT PASS BUT TASK NOT COMPLETED\n---")
print(giactPassedButTaskNotCompleted, "\n")
