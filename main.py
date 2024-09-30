import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
INBOX_SEARCH_FILTER = "from:alerts@hdfcbank.net after:2024/09/24 before:2024/09/30"
TEXT_MATCH = "Dear Card Member, Thank you for using your HDFC Bank Credit Card ending"


def setup_auth():
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

  return creds


def fetch_all_mail_ids(service):
  results = service.users().messages().list(userId="me", q=INBOX_SEARCH_FILTER).execute()
  mails = results.get("messages", [])
  res = []
  mail_ids = []
  res.append(results)

  next_page_token = ""
  if "nextPageToken" in results:
    next_page_token = results["nextPageToken"]

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


def parse_snippet(snippet):
  rs_idx = snippet.index("Rs ")
  at_idx = snippet.index("at ")
  on_idx = snippet.index("on ")
  auth_idx = snippet.index(". Authorization")
  
  amount = snippet[rs_idx+3:at_idx-1]
  place = snippet[at_idx+3:on_idx-1]
  ts = snippet[on_idx+3:auth_idx]

  res = {"amount":amount, "place": place, "ts": ts}
  return res


def get_amount_spent(snippet):
  if snippet.startswith(TEXT_MATCH):
    print(snippet)
    parsed = parse_snippet(snippet)
    return float(parsed["amount"])
  return 0

def main():
  """Fetches mails matching the query pattern,
  parses them to prepare the spend reports
  """
  creds = setup_auth()

  try:
    service = build("gmail", "v1", credentials=creds)
    mail_ids = fetch_all_mail_ids(service)
    snippets = fetch_mail_snippets(service, mail_ids)
    print("got", len(snippets), "snippets")
    with open("snippets.txt", "w" ) as f:
      for item in snippets:
        f.write(f"{item}\n")

    with open("snippets.txt", "r" ) as f:
      lines =  f.readlines()

    total = 0
    for line in lines:
      total += get_amount_spent(line)

    print(total)
  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
