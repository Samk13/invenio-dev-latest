# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 KTH Royal Institute of Technology Sweden
#
# invenio-config-kth is free software, you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file details.

"""Permission configurations."""

# See https://github.com/inveniosoftware/invenio-rdm-records/commit/3253af28cb1ab67c920fe53bc237d2fab5344d82

from flask import current_app
from flask_principal import RoleNeed
from invenio_administration.generators import Administration
from invenio_communities.permissions import CommunityPermissionPolicy
from invenio_records_permissions.generators import Disable, Generator, SystemProcess
from invenio_accounts.utils import resolve_role_id

class CommunityCreator(Generator):
    """Allows users with the configured community-creator role."""

    def needs(self, **kwargs):
        configured = current_app.config.get(
            "CONFIG_COMMUNITY_CREATOR_ROLE", "community-creator"
        )
        role_id = resolve_role_id(configured)
        return [RoleNeed(role_id) if role_id else RoleNeed(configured)]


class CommunitiesPermissionPolicy(CommunityPermissionPolicy):
    """Communities permission policy of KTH.

    This will enable community creator and admins only to create communities.

    deprecating:  https://pypi.org/project/invenio-config-kth/ for versions <= V11.
    """

    can_create = [CommunityCreator(), Administration(), SystemProcess()]

    # Restrict unsafe actions to admins only (remove CommunityOwners)
    can_delete = [Administration(), SystemProcess()]
    can_rename = [Administration(), SystemProcess()]

    can_include_directly = [Disable()]
