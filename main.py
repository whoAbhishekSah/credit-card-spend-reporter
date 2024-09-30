import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
INBOX_SEARCH_FILTER = "from:alerts@hdfcbank.net after:2024/8/30 before:2024/10/31 is:read"

def fetch_all_mail_ids(service):
  results = service.users().messages().list(userId="me", q=INBOX_SEARCH_FILTER).execute()
  mails = results.get("messages", [])
  next_page_token = results["nextPageToken"]
  res = []
  mail_ids = []
  res.append(results)

  print(f"len of mails {len(mails)}")
  while next_page_token != "":
    results = service.users().messages().list(userId="me", q=INBOX_SEARCH_FILTER, pageToken=next_page_token).execute()
    res.append(results)
    if "nextPageToken" in results:
      next_page_token = results["nextPageToken"]
    else:
      next_page_token = ""

  for item in res:
    for mails in item["messages"]:
      mail_ids.append(mails["id"])
  return mail_ids


def fetch_mail_snippet(service, mail_id):
  results = service.users().messages().get(userId="me", id=mail_id).execute()
  return results.get("snippet", [])


def fetch_mail_snippets(service, mail_ids):
  snippets = []
  for idx in mail_ids:
    snippets.append(fetch_mail_snippet(service, idx))
  return snippets


def main():
  """Fetches mails matching the query pattern,
  parses them to prepare the spend reports
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("gmail", "v1", credentials=creds)
    mail_ids = fetch_all_mail_ids(service)
    snippets = fetch_mail_snippets(service, mail_ids)
    print("got", len(snippets), "snippets")
  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
