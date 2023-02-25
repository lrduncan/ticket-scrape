import base64
import logging
import os.path
import sqlite3
from email.message import EmailMessage

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from requests_html import HTMLSession

from constants import MY_EMAIL, SCOPES


def check_used_stock(url: str, price_limit: float):
    """
    Check if the item is in stock at the url, and is below the price limit.
    Currently works for B&H Video, searching used/open box items
    """
    session = HTMLSession()
    r = session.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

    logging.info(f'Searching URL: {url}')

    # This class string seems to be the way to find used/open box item prices
    price_tag = soup.find('span', class_='bond_JJqzY8QbUR')

    if price_tag is None or len(price_tag) == 0:
        logging.info('No used price found')
        if price_limit:
            send_email('Item has no used stock',
                       f'Item no longer has used stock: {url}')
        return None

    price = price_tag.contents[0]
    logging.info(f'Cheapest used price found: {price}')

    # Used price comes with $ in front so remove that and convert to float
    price_as_float = float(str(price).replace('$', ''))

    # Check if we have a price limit and if so, does the current price beat it?
    if price_limit and price_as_float >= price_limit:
        logging.info('Price exceeds limit')
        return price_limit

    item_title_tag = soup.find('h1', class_='text_TAw0W35QK_')
    item_title = item_title_tag.contents[0]

    send_email('New low price for your tracked item!',
               f'''Item {item_title} has a new low price of {price}.\n\n
               Link: {url}''')
    return price_as_float


def send_email(subject, msg):
    logging.info('sending email')
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
        logging.info(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        logging.exception(f'An error occurred: {error}')
        send_message = None
    return send_message


if __name__ == '__main__':
    try:
        con = sqlite3.connect('items.db')
        cur = con.cursor()
        res = cur.execute('SELECT * from items')
        items = res.fetchall()

        for item in items:
            # Items table has columns 'url' and 'price' for each item
            url, price = item
            new_price = check_used_stock(url, price)
            if new_price is None or new_price < price:
                # Update the price according to the latest scrape
                cur.execute('UPDATE items SET price=? WHERE url=?',
                            (new_price, url))
                con.commit()
    except Exception as e:
        send_email('Exception: stock scraper',
                   f'An exception occured within in stock scraper: {e}')
        logging.exception(f'An error occurred: {e}')
