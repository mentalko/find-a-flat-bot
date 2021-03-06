# coding=utf-8
import traceback
import logging
from collections import namedtuple
from datetime import date

import bs4
from bs4 import BeautifulSoup

avito_url = 'https://www.avito.ru'


def parse_price(price_str):
    price = 0
    try:
        for el in price_str.strip().split(' ')[:-1]:
            iprice = int(el)
            price *= 1000
            price += iprice
    finally:
        return price


def parse_time(time_str):
    tl = time_str.strip().split(' ')
    if len(tl) == 2:
        return True
    elif len(tl) == 3:
        if tl[1] == 'мая':
            return True
    return False


def get_img_link(img_tag):
    if not img_tag:
        return
    assert isinstance(img_tag, bs4.element.Tag)
    if img_tag.has_attr('data-srcpath'):
        return img_tag['data-srcpath']
    elif img_tag.has_attr('src'):
        return img_tag['src']
    for chld in img_tag.descendants:
        if isinstance(chld, bs4.element.Tag):
            res = get_img_link(chld)
            if res is not None:
                return res



SimpleAd = namedtuple('Ad', ['id', 'photo', 'title', 'price', 'loc', 'ubahn_dist', 'time', 'link'])


class Ad(SimpleAd):
    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


def get_metro_distance(ad_location):
    elements = ad_location.split(' ')
    distance = 0
    multiplier = 1
    for i in range(len(elements)):
        if elements[i].strip() in ['м,', 'км,']:
            if elements[i].startswith('км'):
                multiplier = 1000
            distance_str = elements[i-1].replace(',', '.')
            return float(distance_str) * multiplier
    logging.info("Couldn't get metro distance for %s", ad_location)
    return 0


def parse_page(html_str):
    result = set()
    soup = BeautifulSoup(html_str, "html5lib")
    cont = soup.find('div', "js-catalog_serp")
    assert isinstance(cont, bs4.element.Tag)

    for elem in cont.find_all('div', recursive=False):
        assert isinstance(elem, bs4.element.Tag)
        if 'avito-ads-container' in elem['class']:
            continue
        if 'item-popup-content' in elem['class']:
            continue
        if 'avito-ads-container' in elem['class']:
            continue
        if 'serp-vips' in elem['class']:
            continue
        try:
            ad_id = elem.get('id')[1:]
            ad_photo_link = get_img_link(elem.find('div', class_='item-slider-image'))
            elem_title = elem.find('h3', 'item-description-title')
            assert isinstance(elem_title, bs4.element.Tag)
            ad_link = elem_title.find('a').get('href')
            ad_title = elem_title.find('a').contents[1].text
            ad_price = parse_price(elem.find('div', 'about').contents[2].text)

            ad_location = elem.find('div', 'address').text.strip()
            if 'м' not in ad_location and 'км' not in ad_location:
                continue
            ad_metro_dist = get_metro_distance(ad_location)
            lil_descr_elem = elem.find('div', 'data')
            ad_time = lil_descr_elem.find('div', 'js-item-date c-2').contents[0]
            ad_time = ad_time.replace('Сегодня', str(date.today().day) + ' ноября')
            ad_time = ad_time.replace('Вчера', str(date.today().day - 1) + ' ноября')
            new_ad = Ad(
                int(ad_id),
                ad_photo_link,
                ad_title.strip(),
                str(ad_price),
                ad_location,
                ad_metro_dist,
                ad_time.strip(),
                avito_url + ad_link
            )
            result.add(new_ad)
        except Exception as ex:
            traceback.print_exc()
            continue
    return result


if __name__ == '__main__':
    with open('page_sample.htm', encoding='utf8') as f:
        dd = f.read()
    for element in parse_page(dd):
        logging.info(element)
    pass
