# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2016 .
# Guijin Ding, dingguijin@gmail.com
#
#

from .basehandler import BaseHandler

from ppmessage.api.error import API_ERR
from ppmessage.db.models import OrgGroup
from ppmessage.db.models import OrgGroupUserData

from ppmessage.core.constant import API_LEVEL
from ppmessage.core.redis import redis_hash_to_dict
from ppmessage.core.utils.createicon import create_user_icon
from ppmessage.core.utils.createicon import create_group_icon

import json
import uuid
import logging

def update_group_icon(_redis, _group_uuid):
    _key = OrgGroupUserData.__tablename__ + ".group_uuid." + _group_uuid
    _users = _redis.smembers(_key)
    _group_icon = None
    if len(_users) == 0:
        _group_icon = create_user_icon(_group_uuid)
    else:
        _group_icon = create_group_icon(_redis, _users)
    _row = OrgGroup(uuid=_group_uuid, group_icon=_group_icon)
    _row.update_redis_keys(_redis)
    _row.async_update(_redis)
    return

class PPAddOrgGroupUserHandler(BaseHandler):

    def _add(self, _group_uuid, _user_uuid):
        _redis = self.application.redis
        _key = OrgGroupUserData.__tablename__ + ".group_uuid." + _group_uuid
        if _redis.sismember(_key, _user_uuid) == True:
            logging.info("user: %s already in group:%s" % (_user_uuid, _group_uuid))
            return

        _row = OrgGroupUserData(uuid=str(uuid.uuid1()), group_uuid=_group_uuid, user_uuid=_user_uuid)
        _row.async_add(_redis)
        _row.create_redis_keys(_redis)
        return
    
    def _get(self, _app_uuid, _group_uuid, _user_list):        
        _redis = self.application.redis
        for _user_uuid in _user_list:
            self._add(_group_uuid, _user_uuid)
        update_group_icon(_redis, _group_uuid)
        return

    def initialize(self):
        self.addPermission(app_uuid=True)
        self.addPermission(api_level=API_LEVEL.PPCONSOLE)
        self.addPermission(api_level=API_LEVEL.THIRD_PARTY_CONSOLE)
        return
    
    def _Task(self):
        super(PPAddOrgGroupUserHandler, self)._Task()
        _body = json.loads(self.request.body)
        _app_uuid = _body.get("app_uuid")
        _user_list = _body.get("user_list")
        _group_uuid = _body.get("group_uuid")
        if _app_uuid == None or _group_uuid == None or _user_list == None:
            self.setErrorCode(API_ERR.NO_PARA)
            return

        if not isinstance(_user_list, list):
            self.setErrorCode(API_ERR.NOT_LIST)
            return

        self._get(_app_uuid, _group_uuid, _user_list)
        return
