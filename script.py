import requests

import json

from datetime import datetime, date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

f = open("config.json")

config = json.load(f)

# Defining Access Token

ACCESSTOKEN = config["ACCESSTOKEN"]
ACCESSTOKENHEADER = "access_token=" + ACCESSTOKEN

# Facebook Graph API URL

URL = config["URL"]

creds = Credentials.from_service_account_file(
    "credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

# Defining Campaign ID

CAMPAIGN_SPREADSHEET_LINK = config["CAMPAIGN_SPREADSHEET_LINK"]

for client in CAMPAIGN_SPREADSHEET_LINK:
    CAMPAIGNIDS = client["CAMPAIGNIDS"]

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
        if not response["data"]:
            print(response)
            exit()

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
                + "date_preset=yesterday"
            ).json()

            print(response)

            if not response["data"]:
                continue

            response4name = requests.get(
                URL + adset["id"] + "?" + ACCESSTOKENHEADER + "&" + "fields=name"
            ).json()

            involvedAdSets.append(response4name["name"].split()[ADSET_NAMENUMBERINDEX])

            if "impressions" in response["data"][0]:
                impressions += float(response["data"][0]["impressions"])
            if "spend" in response["data"][0]:
                adspend += float(response["data"][0]["spend"])
            if "clicks" in response["data"][0]:
                click_all += float(response["data"][0]["clicks"])
            if "inline_link_clicks" in response["data"][0]:
                link_clicks += float(response["data"][0]["inline_link_clicks"])

    # The ID of spreadsheet.
    SPREADSHEET_ID = client["SPREADSHEET_ID"]

    SHEETNAME = config["SHEETNAME"]

    TEXT2DATEFORMAT = "%d %b %Y, %a"

    DATESEARCHLIMIT = 1000

    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """

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

        yesteday = date.today() - timedelta(days=1)

        if not values:
            print("No data found.")
        else:
            for index, row in enumerate(values):
                # Print columns A and E, which correspond to indices 0 and 4.
                checkDate = datetime.strptime(row[0], TEXT2DATEFORMAT)

                if (
                    checkDate.day == yesteday.day
                    and checkDate.month == yesteday.month
                    and checkDate.year == yesteday.year
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

        print(client["NAME"], "Updated for", yesteday.strftime("%d %b %Y, %a"))

    except HttpError as err:
        print(err)
