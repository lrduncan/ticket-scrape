from requests_html import HTMLSession
from bs4 import BeautifulSoup

def check_used_stock(url:str, price_limit:float):
    session = HTMLSession()
    r = session.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')

    price_tag = soup.find('span', class_='bond_JJqzY8QbUR')

    if price_tag == None or len(price_tag) == 0:
        return 'No used price found'
    
    price = price_tag.contents[0]
    print(f'Cheapest used price found: {price}')

    # Used price comes with $ in front so remove that and convert to float
    price_as_float = float(str(price).replace('$', ''))

    if price_as_float > price_limit:
        return 'Price exceeds limit'
    
def send_email():
    # TODO
    print('sending email')



if __name__ == '__main__':
    # Enter site url here
    url = 'https://www.bhphotovideo.com/c/product/1466512-REG/sky_watcher_s11705_heritage_130mm_f_5_tabletop.html'

    check_used_stock(url, 219.95)
