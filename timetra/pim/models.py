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

from monk import (
    manipulation, modeling, one_of, IsA, Length, Equals, translate, nullable,
    optional, opt_key,
)

from . import compat
from . import utils   # for Concern.sorted_plans


if compat.PY3:
    unicode = str


__all__ = ['Concern', 'contact_schema', 'asset_schema', 'project_schema']


#--- Pure Schemata


log_schema = {
    'time': datetime.datetime,
    opt_key('note'): nullable(unicode),
    'data': dict,
}


referenced_item_schema = [unicode]    # Rule(list, inner_spec=unicode)
referenced_items_schema = translate({
    opt_key('assets'): referenced_item_schema,
    opt_key('contacts'): referenced_item_schema,
    opt_key('projects'): referenced_item_schema,
    opt_key('reference'): referenced_item_schema,
}) & Length(min=1)


STATUS_TODO = u'todo'
STATUS_WAITING = u'waiting'
STATUS_DONE = u'done'
STATUS_CANCELLED = u'cancelled'

plan_status_choices = STATUS_TODO, STATUS_WAITING, STATUS_DONE, STATUS_CANCELLED

plan_schema = {
    'action': unicode,
    'status': one_of(plan_status_choices, first_is_default=True),
    opt_key('refers'): referenced_items_schema,
    opt_key('repeat'): unicode,
    opt_key('effort'): unicode,
    opt_key('context'): [u'anywhere'],
    opt_key('srcmeta'): dict,
    opt_key('delegated'): unicode,
    opt_key('log'): [ log_schema ],
    opt_key('opened'): nullable(datetime.datetime),
    opt_key('closed'): nullable(datetime.datetime),
    opt_key('result'): nullable(unicode),  # комментарий о результате выполнения действия: грабли, особенности, ...
    opt_key('reqs'): [unicode],    # требования (напр., какие документы нужно принести и т.д.)
    opt_key('time'): datetime.datetime,
}


concern_schema = {
    opt_key('note'): unicode,
    'risk': nullable(unicode),
    'need': nullable(unicode),
    opt_key('haze'): unicode,  # неясность; вопросы, требующие прояснения. mess, uncertainty
    opt_key('plan'): [
        plan_schema
    ],
    opt_key('date'): datetime.date,
    opt_key('cost'): dict(
        amount = float,
        currency = unicode,
    ),
    opt_key('stakeholders'): [unicode],
    opt_key('project'): unicode,
    'acute': False,
    'opened': nullable(datetime.datetime),
    'closed': nullable(datetime.datetime),
    opt_key('solved'): nullable(False),
    opt_key('frozen'): datetime.datetime,  # if not None, it's someday/maybe
    opt_key('revive'): datetime.date,      # if set, the concern is not considered frozen anymore since given date
    opt_key('refers'): referenced_items_schema,
    opt_key('reqs'): [unicode],            # list of items that block this one
    # TODO:
    # * проблема/потребность со временем: не меняется / усугубляется / ослабевает
    opt_key('log'): [ log_schema ],
}


contact_schema = {
    'name': unicode,
    opt_key('full_name'): unicode,
    opt_key('urls'): [unicode],
    opt_key('addr'): unicode,
    opt_key('tels'): [unicode],
    opt_key('mail'): [unicode],
    opt_key('note'): unicode,
    opt_key('nick'): unicode,
    opt_key('born'): datetime.date,
    opt_key('related'): [unicode],    # hashtags
    opt_key('first_contact'): datetime.date,
    opt_key('org'): unicode,
    opt_key('timetable'): unicode,
    opt_key('concerns'): [
        concern_schema
    ],
}


imei_schema = IsA(unicode) & Length(max=15)


ASSET_CONDITION_CHOICES = u'new', u'good', u'fair', u'poor', u'unusable'
ASSET_OWNING_STATE_CHOICES = u'in effect', u'ordered', u'discarded', u'sold', u'given away'


asset_schema = {
    'name': unicode,
    'usable': True,
    opt_key('urls'): [unicode],
    opt_key('note'): unicode,
    opt_key('type'): unicode,
    opt_key('physical'): {
        #'condition'): Rule(unicode, validators=[validators.validate_choice(['new'])],
        'condition': one_of(ASSET_CONDITION_CHOICES),
        opt_key('maker'): unicode,
        opt_key('model'): unicode,
        opt_key('size'): unicode,
        opt_key('weight'): unicode,
        opt_key('colour'): unicode,
        opt_key('location'): unicode,  # maybe hashtag
        opt_key('quantity'): int,
        opt_key('manufactured'): unicode,  # free-form date
        opt_key('volume'): unicode,    # storage volume, be it litres or bytes
        opt_key('connectivity'): unicode,
        opt_key('material'): unicode,
    },
    opt_key('owning'): {
        opt_key('state'): one_of(ASSET_OWNING_STATE_CHOICES, first_is_default=True),
        opt_key('owner'): unicode,
        opt_key('price'): unicode,  # may include currency
        opt_key('vendor'): unicode,
        opt_key('bought'): datetime.date,
        opt_key('delivered'): datetime.date, # free-form date
    },
    opt_key('stakeholders'): list,  # hashtags
    # meta
    opt_key('mail_label'): unicode,    # gmail integration
    opt_key('categories'): [unicode],
    # Недвижимость
    opt_key('flat'): {
        'addr': unicode,
        opt_key('cadastre_zone'): unicode,
        opt_key('title_deed'): int,
        opt_key('unit'): unicode,
        opt_key('overall_area'): unicode,         # общая площадь
        opt_key('living_space'): unicode,         # жилая площадь
        opt_key('residents_num'): int,            # количество проживающих
        opt_key('ownership_form'): unicode,       # форма собственности
    },
    # Устройства/техника
    opt_key('device'): {
        # device model
        opt_key('model_number'): unicode,
        opt_key('model_code'): unicode,
        opt_key('product_code'): unicode,
        opt_key('product_name'): unicode,
        opt_key('product_number'): unicode,
        opt_key('article'): unicode,           # артикул
        opt_key('standard'): unicode,          # IEEE, ГОСТ, ...
        # this device
        opt_key('serial_number'): unicode,
        opt_key('mac_address_eth'): unicode,
        opt_key('mac_address_wlan'): unicode,
        opt_key('mac_address_bluetooth'): unicode,
        #'imei'): optional(int),  # XXX вот тут бы проверить кол-во знаков!
        opt_key('imei'): imei_schema,
        opt_key('hardware_version'): unicode,
        opt_key('software_version'): unicode,
    },
    # Доменные имена
    opt_key('domain_name'): {
        'registrar': unicode,
        opt_key('username'): unicode,
    },
    # Счета
    opt_key('account'): dict,
    # Мебель
    opt_key('furniture'): dict,
    # Одежда, обувь
    opt_key('clothes'): dict,
    # Музыкальные инструменты
    opt_key('music'): dict,
    # Услуги
    opt_key('service'): dict,
    opt_key('concerns'): [
        optional(concern_schema)
    ],
}


project_schema = {
    'name': unicode,
    'state': unicode,
    opt_key('urls'): [unicode],
    opt_key('note'): unicode,
    opt_key('mail_label'): [unicode],
    'concerns': [
        optional(concern_schema)
    ],
    opt_key('stakeholders'): list,  # hashtags
    opt_key('categories'): [unicode],
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
            data['context'] = manipulation.normalize_to_list(data['context'])

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

        if 'plan' in data:
            # разворачиваем строку или словарь в список словарей
            data['plan'] = manipulation.normalize_list_of_dicts(data.get('plan'), 'action')

            # заворачиваем строку в список
            data['plan'] = [Plan(**x) for x in data['plan']]

        super(Concern, self).__init__(**data)

    def _check_has_plan(self, status):
        status_list = (status,) if isinstance(status, unicode) else status
        if not self.get('plan'):
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
        if self.get('plan'):
            if any(x.get('delegated') for x in self.plan if not x.get('closed')):
                return True
        return self._check_has_plan(Plan.STATUS_WAITING)

    def is_frozen(self):
        "Returns `True` if concern is frozen and not (yet) revived."
        if not self.get('frozen'):
            return False
        if self.get('revive') and (
            utils.to_date(self.revive) <= datetime.date.today()):
            return False
        return True

    def sorted_plans(self):
        if not self.get('plan'):
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
