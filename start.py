import requests
from bs4 import BeautifulSoup

def check_stock(url):
    r = requests.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

if __name__ == '__main__':
    # Enter site url here
    url = ''

    check_stock(url)