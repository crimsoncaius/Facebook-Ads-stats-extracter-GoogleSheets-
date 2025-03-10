import requests

import os.path
import json

from datetime import datetime, date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


f = open("config.json")

config = json.load(f)

start_date = datetime.strptime(config["DATERANGEFORBACKLOG"][0], "%d %B %Y")
end_date = datetime.strptime(config["DATERANGEFORBACKLOG"][1], "%d %B %Y")

# Defining Access Token

ACCESSTOKEN = config["ACCESSTOKEN"]
ACCESSTOKENHEADER = "access_token=" + ACCESSTOKEN

# Facebook Graph API URL

URL = config["URL"]

# Defining Campaign ID

CAMPAIGNIDS = config["CAMPAIGNIDS"]


for single_date in daterange(start_date, end_date):
    # Initialising Variables

    impressions = 0
    adspend = 0
    click_all = 0
    link_clicks = 0
    involvedAdSets = []

    for campaignID in CAMPAIGNIDS:
        response = requests.get(
            URL + campaignID + "/adsets" + "?" + ACCESSTOKENHEADER
        ).json()

        ADSET_NAMENUMBERINDEX = config["ADSET_NAMENUMBERINDEX"]

        # Computing the sums for the day

        # processing to the right format
        current_date = single_date.strftime("%Y-%m-%d")

        for adset in response["data"]:
            response = requests.get(
                URL
                + adset["id"]
                + "/insights"
                + "?"
                + ACCESSTOKENHEADER
                + "&"
                + "fields=impressions,spend,clicks,inline_link_clicks"
                + "&"
                + f"time_range[since]={current_date}"
                + "&"
                + f"time_range[until]={current_date}"
            ).json()

            print(response)

            if not response["data"]:
                continue

            response4name = requests.get(
                URL + adset["id"] + "?" + ACCESSTOKENHEADER + "&" + "fields=name"
            ).json()

            involvedAdSets.append(
                int(response4name["name"].split()[ADSET_NAMENUMBERINDEX])
            )

            if "impression" in response["data"][0]:
                impressions += float(response["data"][0]["impressions"])
            if "spend" in response["data"][0]:
                adspend += float(response["data"][0]["spend"])
            if "clicks" in response["data"][0]:
                click_all += float(response["data"][0]["clicks"])
            if "inline_link_clicks" in response["data"][0]:
                link_clicks += float(response["data"][0]["inline_link_clicks"])

        involvedAdSets.sort()
        involvedAdSets = map(str, involvedAdSets)

    print("involvedAdSets", involvedAdSets)
    print("Stats", impressions, adspend, click_all, link_clicks)

    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # The ID of spreadsheet.
    SPREADSHEET_ID = config["SPREADSHEET_ID"]

    SHEETNAME = config["SHEETNAME"]

    TEXT2DATEFORMAT = config["TEXT2DATEFORMAT"]

    DATESEARCHLIMIT = config["DATESEARCHLIMIT"]

    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.

    indexToChange = 0

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()

        result = (
            sheet.values()
            .get(
                spreadsheetId=SPREADSHEET_ID, range=f"{SHEETNAME}!A2:A{DATESEARCHLIMIT}"
            )
            .execute()
        )

        values = result.get("values", [])

        if not values:
            print("No data found.")
        else:
            for index, row in enumerate(values):
                # Print columns A and E, which correspond to indices 0 and 4.
                checkDate = datetime.strptime(row[0], config["TEXT2DATEFORMAT"])

                if (
                    checkDate.day == single_date.day
                    and checkDate.month == single_date.month
                    and checkDate.year == single_date.year
                ):
                    indexToChange = index + 2
                    break

        # impressions to gsheet
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEETNAME}!G{indexToChange}",
            valueInputOption="USER_ENTERED",
            body={"values": [[str(impressions)]]},
        ).execute()

        # adspend to gsheet
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEETNAME}!F{indexToChange}",
            valueInputOption="USER_ENTERED",
            body={"values": [[str(adspend)]]},
        ).execute()

        # click_all to gsheet
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEETNAME}!H{indexToChange}",
            valueInputOption="USER_ENTERED",
            body={"values": [[str(click_all)]]},
        ).execute()

        # link_clicks to gsheet
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEETNAME}!I{indexToChange}",
            valueInputOption="USER_ENTERED",
            body={"values": [[str(link_clicks)]]},
        ).execute()

        # involvedAdSets to gsheet
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEETNAME}!E{indexToChange}",
            valueInputOption="USER_ENTERED",
            body={"values": [[",".join(involvedAdSets)]]},
        ).execute()

    except HttpError as err:
        print(err)
