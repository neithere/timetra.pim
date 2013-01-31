# -*- coding: utf-8 -*-
import datetime
from monk.validation import optional


CARD = {
    'name': unicode,
    'full_name': optional(unicode),
    'urls': optional([unicode]),
    'addr': optional(unicode),
    'tels': optional([unicode]),
    'mail': optional([unicode]),
    'note': optional(unicode),
    'nick': optional(unicode),
    'born': optional(datetime.date),
    'related': optional([unicode]),    # hashtags
    'first_contact': optional(datetime.date),
    'org': optional(unicode),
    'timetable': optional(unicode),
}


ASSET = {
    'name': unicode,
    'state': unicode,
    'urls': optional([unicode]),
    'price': optional(unicode),  # may include currency
    'note': optional(unicode),
    'type': optional(unicode),
    'physical': optional({
        'maker': optional(unicode),
        'model': optional(unicode),
        'size': optional(unicode),
        'weight': optional(unicode),
        'colour': optional(unicode),
        'location': optional(unicode),  # maybe hashtag
        'quantity': optional(int),
        'manufactured': optional(unicode),  # free-form date
        'volume': optional(unicode),    # storage volume, be it litres or bytes
        'connectivity': optional(unicode),
    }),
    'owning': optional(dict),
    'stakeholders': optional(list),  # hashtags
    # meta
    'mail_label': optional(unicode),    # gmail integration
    'categories': optional([unicode]),
    # Недвижимость
    'flat': optional({
        'addr': unicode,
        'cadastre_zone': optional(unicode),
        'title_deed': optional(int),
        'unit': optional(unicode),
        'overall_area': optional(unicode),         # общая площадь
        'living_space': optional(unicode),         # жилая площадь
        'residents_num': optional(int),            # количество проживающих
        'ownership_form': optional(unicode),       # форма собственности
    }),
    # Устройства/техника
    'device': optional({
        # device model
        'product_code': optional(unicode),
        'product_name': optional(unicode),
        'product_number': optional(unicode),
        'article': optional(unicode),           # артикул
        'standard': optional(unicode),          # IEEE, ГОСТ, ...
        # this device
        'serial_number': optional(unicode),
        'mac_address_eth': optional(unicode),
        'mac_address_wlan': optional(unicode),
        'mac_address_bluetooth': optional(unicode),
        'imei': optional(int),  # XXX вот тут бы проверить кол-во знаков!
        'hardware_version': optional(unicode),
        'software_version': optional(unicode),
    }),
    # Доменные имена
    'domain_name': optional({
        'registrar': unicode,
        'username': optional(unicode),
    }),
    # Счета
    'account': optional(dict),
    # Мебель
    'furniture': optional(dict),
    # Одежда, обувь
    'clothes': optional(dict),
    # Музыкальные инструменты
    'music': optional(dict),
    # Услуги
    'service': optional(dict),
}


PROJECT = {
    'name': unicode,
    'state': unicode,
    'urls': optional([unicode]),
    'note': optional(unicode),
    'mail_label': optional([unicode]),
    'concerns': list,
    'stakeholders': optional(list),  # hashtags
    'categories': optional([unicode]),
}
