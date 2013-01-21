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
    'maker': optional(unicode),
    'model': unicode,
    'price': optional(unicode),  # may include currency
    'note': optional(unicode),
    'type': optional(unicode),
    'manufactured': optional(unicode),  # free-form date
    'physical': optional({
        'size': optional(unicode),
        'weight': optional(unicode),
        'colour': optional(unicode),
        'location': optional(unicode),  # maybe hashtag
        'quantity': optional(int),
    }),
    'owning': optional(dict),
    'stakeholders': optional(list),  # hashtags
    # meta
    'mail_label': optional(unicode),    # gmail integration
    'categories': optional([unicode]),
    # by class:
    'flat': optional({
        'addr': unicode,
    }),
    'device': optional({
        'serial_number': unicode,
    }),
    'account': optional(dict),
    'furniture': optional(dict),
    'clothes': optional(dict),
    'music': optional(dict),
    'service': optional(dict),
}
