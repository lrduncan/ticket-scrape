from requests_html import HTMLSession
from bs4 import BeautifulSoup
from constants import MY_EMAIL, ITEMS, SCOPES
from time import sleep, gmtime, strftime

import base64
from email.message import EmailMessage

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def check_used_stock(url: str, price_limit: float):
    """
    Check if the item is in stock at the url, and is below the price limit.
    Currently works for B&H Video, searching used/open box items
    """
    session = HTMLSession()
    r = session.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

    print(f'Searching URL: {url}')

    # This class string seems to be the way to find used/open box item prices
    price_tag = soup.find('span', class_='bond_JJqzY8QbUR')

    if price_tag is None or len(price_tag) == 0:
        print('No used price found')
        if price_limit:
            send_email('Item has no used stock', f'Item no longer has used stock: {url}')
        return

    price = price_tag.contents[0]
    print(f'Cheapest used price found: {price}')

    # Used price comes with $ in front so remove that and convert to float
    price_as_float = float(str(price).replace('$', ''))

    # Check if we have a price limit and if so, does the current price beat it?
    if price_limit and price_as_float >= price_limit:
        print('Price exceeds limit')
        return

    item_title_tag = soup.find('h1', class_='text_TAw0W35QK_')
    item_title = item_title_tag.contents[0]

    send_email('New low price for your tracked item!',
        f'Item {item_title} has a new low price of {price}.\n\n Link: {url}')


def send_email(subject, msg):
    print('sending email')
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(msg)

        message['To'] = MY_EMAIL
        message['From'] = MY_EMAIL
        message['Subject'] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')
        send_message = None
    return send_message


if __name__ == '__main__':

    items = ITEMS

    while True:
        try:
            print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))

            for item in items:
                check_used_stock(item['url'], item['price'])

            sleep_time = 15 * 60
            print(f'Sleeping for {sleep_time} seconds, or {int(sleep_time/60)} minutes')
            sleep(sleep_time)
        except Exception as e:
            send_email('Exception: stock scraper', f'An exception occured within in stock scraper: {e}')
