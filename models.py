# -*- coding: utf-8 -*-

import datetime

from monk import manipulation, modeling
from monk.validation import optional

import utils   # for Concern.sorted_plans


__all__ = ['Concern', 'CONTACT', 'ASSET', 'PROJECT']


class Model(modeling.TypedDictReprMixin,
            modeling.DotExpandedDictMixin,
            modeling.StructuredDictMixin,
            dict):

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        self._insert_defaults()
        self._make_dot_expanded()


class Log(Model):
    """ A log record.

    The :attr:`data` dictionary contains newly set values of the parent object.
    """
    structure = dict(
        time = datetime.datetime,
        note = unicode,
        data = dict,
    )


class Plan(Model):
    """ A planned activity.
    """
    STATUS_TODO = u'todo'
    STATUS_WAITING = u'waiting'
    STATUS_DONE = u'done'
    STATUS_CANCELLED = u'cancelled'

    structure = dict(
        action = unicode,
        status = STATUS_TODO,
        repeat = unicode,
        effort = unicode,
        context = [unicode],
        srcmeta = dict,
        delegated = unicode,
        log = [Log.structure],
        opened = datetime.datetime,
        closed = datetime.datetime,
        result = unicode,  # комментарий о результате выполнения действия: грабли, особенности, ...
        reqs = [unicode],    # требования (напр., какие документы нужно принести и т.д.)
        time = datetime.datetime,
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        if 'context' in data:
            data['context'] = manipulation.unfold_to_list(data['context'])

        # convert date to datetime
        for key in ('opened', 'closed'):
            if key in data and isinstance(data[key], datetime.date):
                data[key] = utils.to_datetime(data[key])

        super(Plan, self).__init__(**data)


class Concern(Model):
    """ An item containing observation, problem definition, goal and plan.
    """
    structure = dict(
        note = unicode,
        risk = unicode,
        need = unicode,
        haze = unicode,  # неясность; вопросы, требующие прояснения. mess, uncertainty
        plan = [Plan.structure],
        date = datetime.date,
        cost = dict(
            amount = float,
            currency = unicode,
        ),
        stakeholders = [unicode],
        project = unicode,
        acute = False,
        opened = datetime.datetime,
        closed = datetime.datetime,
        solved = False,
        frozen = datetime.datetime,  # if not None, it's someday/maybe
        revive = datetime.date,      # if set, the concern is not considered frozen anymore since given date
        reqs = [unicode],            # list of items that block this one
        # TODO:
        # * проблема/потребность со временем: не меняется / усугубляется / ослабевает
        log = [Log.structure]
    )

    def __init__(self, **kwargs):
        data = kwargs.copy()

        # convert date to datetime
        for key in ('opened', 'closed'):
            if key in data and isinstance(data[key], datetime.date):
                data[key] = utils.to_datetime(data[key])

        # разворачиваем строку или словарь в список словарей
        data['plan'] = manipulation.unfold_list_of_dicts(data.get('plan'), 'action')

        # заворачиваем строку в список
        data['plan'] = [Plan(**x) for x in data['plan']]

        super(Concern, self).__init__(**data)

    def _check_has_plan(self, status):
        status_list = (status,) if isinstance(status, unicode) else status
        if not self.plan:
            return False
        for plan in self.plan:
            if plan.status in status_list:
                return True
        return False

    def has_next_action(self):
        return self._check_has_plan((Plan.STATUS_TODO, Plan.STATUS_WAITING))

    def has_completed_action(self):
        return self._check_has_plan(Plan.STATUS_DONE)

    def is_waiting(self):
        if self.plan:
            if any(x.delegated for x in self.plan if not x.closed):
                return True
        return self._check_has_plan(Plan.STATUS_WAITING)

    def sorted_plans(self):
        if not self.plan:
            return []
        return sorted(self.plan, key=lambda x: utils.to_datetime(x.closed or
                                               datetime.datetime.now()))

    @property
    def completed_percentage(self):
        if not self.plan:
            return 0
        total_cnt = len([x for x in self.plan])
        if not total_cnt:
            return 0
        closed_cnt = len([x for x in self.plan if x.closed])
        return (float(closed_cnt) / total_cnt) * 100


class Document(Model):
    """ An item with slug, title and body.
    """
    structure = dict(
        title = unicode,
        slug = unicode,
        body = unicode,
        categories = [unicode],
    )


#--- Pure Schemata


CONTACT = {
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
    'concerns': optional([Concern.structure]),
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
        'material': optional(unicode),
    }),
    'owning': optional({
        'owner': optional(unicode),
        'vendor': optional(unicode),
        'bought': optional(datetime.date),
        'delivered': optional(datetime.date), # free-form date
    }),
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
        'model_number': optional(unicode),
        'model_code': optional(unicode),
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
    'concerns': optional([Concern.structure]),
}


PROJECT = {
    'name': unicode,
    'state': unicode,
    'urls': optional([unicode]),
    'note': optional(unicode),
    'mail_label': optional([unicode]),
    'concerns': optional([Concern.structure]),
    'stakeholders': optional(list),  # hashtags
    'categories': optional([unicode]),
}
