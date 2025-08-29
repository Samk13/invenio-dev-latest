# -*- coding: utf-8 -*-
#
# Simplified check for testing purposes on InvenioRDM.
#
# Usage:

# .. code-block:: shell

#     invenio shell create_checks.py
# """

from invenio_checks.models import CheckConfig, Severity
from invenio_communities.proxies import current_communities
from invenio_db import db
from werkzeug.local import LocalProxy

community_service = LocalProxy(lambda: current_communities.service)

COMMUNITY_SLUG = "test"
# Minimal ruleset: only check that metadata.rights exists
RIGHTS_RULES = {
    "rules": [
        {
            "id": "license:cc-by-4.0",
            "title": "Record license must be CC BY 4.0",
            "message": "All submissions must specify the CC BY 4.0 license",
            "description": "Submissions are required to be licensed under CC BY 4.0.",
            "level": "error",
            "checks": [
                {
                    "type": "list",
                    "operator": "any",
                    "path": "metadata.rights",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "id"},
                        "operator": "==",
                        "right": "cc-by-4.0",
                    },
                }
            ],
        }
    ]
}


def create_rights_check(community_slug=COMMUNITY_SLUG):
    """Create or update metadata.rights check for given community."""
    comm = community_service.record_cls.pid.resolve(community_slug)

    existing_check = CheckConfig.query.filter_by(
        community_id=comm.id, check_id="metadata"
    ).one_or_none()

    if existing_check:
        existing_check.params = RIGHTS_RULES
    else:
        check_config = CheckConfig(
            community_id=comm.id,
            check_id="metadata",
            params=RIGHTS_RULES,
            severity=Severity.INFO,
            enabled=True,
        )
        db.session.add(check_config)

    db.session.commit()
    print(f"Metadata.rights check created/updated successfully for {comm.slug}.")


if __name__ == "__main__":
    create_rights_check()
