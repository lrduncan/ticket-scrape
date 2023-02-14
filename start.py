from requests_html import HTMLSession
from bs4 import BeautifulSoup

def check_stock(url):
    session = HTMLSession()
    r = session.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

    print(soup.find_all('span'))


if __name__ == '__main__':
    # Enter site url here
    url = 'https://www.bhphotovideo.com/c/product/1466512-REG/sky_watcher_s11705_heritage_130mm_f_5_tabletop.html'

    check_stock(url)
