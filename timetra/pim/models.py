# coding: utf-8
#
#    Timetra is a time tracking application and library.
#    Copyright © 2010-2014  Andrey Mikhaylenko
#
#    This file is part of Timetra.
#
#    Timetra is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Timetra is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Timetra.  If not, see <http://gnu.org/licenses/>.
#

import datetime

from monk import manipulation, modeling, validators
from monk.schema import Rule, one_of, optional

from . import compat
from . import utils   # for Concern.sorted_plans


if compat.PY3:
    unicode = str


__all__ = ['Concern', 'contact_schema', 'asset_schema', 'project_schema']


#--- Pure Schemata


log_schema = dict(
    time = datetime.datetime,
    note = optional(unicode),
    data = dict,
)


referenced_item_schema = [unicode]    # Rule(list, inner_spec=unicode)
referenced_items_schema = {
    'assets': optional(referenced_item_schema),
    'contacts': optional(referenced_item_schema),
    'projects': optional(referenced_item_schema),
    'reference': optional(referenced_item_schema),
}


STATUS_TODO = u'todo'
STATUS_WAITING = u'waiting'
STATUS_DONE = u'done'
STATUS_CANCELLED = u'cancelled'

plan_status_choices = STATUS_TODO, STATUS_WAITING, STATUS_DONE, STATUS_CANCELLED

plan_schema = dict(
    action = unicode,
    status = one_of(plan_status_choices, first_is_default=True),
    refers = optional(referenced_items_schema),
    repeat = optional(unicode),
    effort = optional(unicode),
    context = Rule(list, inner_spec=unicode, default=[u'anywhere']),
    srcmeta = optional(dict),
    delegated = optional(unicode),
    log = optional([
        optional(log_schema)
    ]),
    opened = optional(datetime.datetime),
    closed = optional(datetime.datetime),
    result = optional(unicode),  # комментарий о результате выполнения действия: грабли, особенности, ...
    reqs = optional([unicode]),    # требования (напр., какие документы нужно принести и т.д.)
    time = optional(datetime.datetime),
)


concern_schema = dict(
    note = optional(unicode),
    risk = optional(unicode),
    need = optional(unicode),
    haze = optional(unicode),  # неясность; вопросы, требующие прояснения. mess, uncertainty
    plan = optional([
        optional(plan_schema)
    ]),
    date = optional(datetime.date),
    cost = optional(dict(
        amount = float,
        currency = unicode,
    )),
    stakeholders = optional([unicode]),
    project = optional(unicode),
    acute = False,
    opened = optional(datetime.datetime),
    closed = optional(datetime.datetime),
    solved = False,
    frozen = optional(datetime.datetime),  # if not None, it's someday/maybe
    revive = optional(datetime.date),      # if set, the concern is not considered frozen anymore since given date
    refers = optional(referenced_items_schema),
    reqs = optional([unicode]),            # list of items that block this one
    # TODO:
    # * проблема/потребность со временем: не меняется / усугубляется / ослабевает
    log = optional([
        optional(log_schema)
    ]),
)


contact_schema = {
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
    'concerns': optional([
        optional(concern_schema)
    ]),
}


imei_schema = Rule(unicode, validators=[validators.validate_length(15)])


ASSET_CONDITION_CHOICES = u'new', u'good', u'fair', u'poor', u'unusable'
ASSET_OWNING_STATE_CHOICES = u'in effect', u'ordered', u'discarded', u'sold', u'given away'


asset_schema = {
    'name': unicode,
    'usable': True,
    'urls': optional([unicode]),
    'note': optional(unicode),
    'type': optional(unicode),
    'physical': optional({
        #'condition': Rule(unicode, validators=[validators.validate_choice(['new'])]),
        'condition': one_of(ASSET_CONDITION_CHOICES),
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
        'state': optional(one_of(ASSET_OWNING_STATE_CHOICES, first_is_default=True)),
        'owner': optional(unicode),
        'price': optional(unicode),  # may include currency
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
        #'imei': optional(int),  # XXX вот тут бы проверить кол-во знаков!
        'imei': optional(imei_schema),
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
    'concerns': optional([
        optional(concern_schema)
    ]),
}


project_schema = {
    'name': unicode,
    'state': unicode,
    'urls': optional([unicode]),
    'note': optional(unicode),
    'mail_label': optional([unicode]),
    'concerns': optional([
        optional(concern_schema)
    ]),
    'stakeholders': optional(list),  # hashtags
    'categories': optional([unicode]),
}

#CONTACT = contact_schema
#ASSET = asset_schema
#PROJECT = project_schema
#REFERENCED_ITEM = referenced_item_schema
#REFERENCED_ITEMS = referenced_items_schema


#--- Schema-Based Object Definitions


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
    structure = log_schema


class Plan(Model):
    """ A planned activity.
    """


    structure = plan_schema

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
    structure = concern_schema

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

    def is_frozen(self):
        "Returns `True` if concern is frozen and not (yet) revived."
        if not self.frozen:
            return False
        if self.revive and (
            utils.to_date(self.revive) <= datetime.date.today()):
            return False
        return True

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
