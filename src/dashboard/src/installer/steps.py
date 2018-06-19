# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import logging
import uuid

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from tastypie.models import ApiKey

from main.models import Agent, DashboardSetting, User
import components.helpers as helpers
import storageService as storage_service
from version import get_version


logger = logging.getLogger('archivematica.dashboard')


def create_super_user(username, email, password, key):
    UserModel = get_user_model()
    user = UserModel._default_manager.db_manager('default').create_superuser(username, email, password)
    api_key = ApiKey.objects.create(user=user)
    api_key.key = key
    api_key.save()


def setup_pipeline(org_name, org_identifier, site_url):
    # Assign UUID to Dashboard
    dashboard_uuid = str(uuid.uuid4())
    helpers.set_setting('dashboard_uuid', dashboard_uuid)

    # Update Archivematica version in DB
    archivematica_agent = Agent.objects.get(pk=1)
    archivematica_agent.identifiervalue = "Archivematica-" + get_version()
    archivematica_agent.save()

    if org_name != '' or org_identifier != '':
        agent = get_agent()
        agent.name = org_name
        agent.identifiertype = 'repository code'
        agent.identifiervalue = org_identifier
        agent.save()

    if site_url:
        helpers.set_setting('site_url', site_url)


def setup_pipeline_in_ss(use_default_config=False):
    if not use_default_config:
        # Storage service manually set up, just register Pipeline if
        # possible. Do not provide additional information about the shared
        # path, or API, as this is probably being set up in the storage
        # service manually.
        storage_service.create_pipeline()
        return

    # Post first user & API key
    user = User.objects.all()[0]
    api_key = ApiKey.objects.get(user=user)

    # Retrieve remote name
    try:
        setting = DashboardSetting.objects.get(name='site_url')
    except DashboardSetting.DoesNotExist:
        remote_name = None
    else:
        remote_name = setting.value

    # Create pipeline, tell it to use default setup
    storage_service.create_pipeline(
        create_default_locations=True,
        shared_path=django_settings.SHARED_DIRECTORY,
        remote_name=remote_name,
        api_username=user.username,
        api_key=api_key.key,
    )


def get_agent():
    return Agent.objects.get(pk=2)
