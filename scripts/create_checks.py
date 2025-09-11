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
            "message": {
                "en": "All submissions must specify the CC BY 4.0 license",
                "sv": "Alla inskickade arbeten måste ange CC BY 4.0-licensen",
                "de": "Alle Einreichungen müssen die CC BY 4.0-Lizenz angeben",
            },
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
        },
        {
            "id": "access:open/publication",
            "title": {
                "en": "Open Access Publication",
                "sv": "Öppen tillgång publikation",
                "de": "Open-Access-Publikation",
            },
            "message": {
                "en": "Publication articles must be Open Access",
                "sv": "Publikationsartiklar måste vara öppen tillgång",
                "de": "Publikationsartikel müssen Open Access sein",
            },
            "description": {
                "en": "The EU curation policy requires publication articles must be Open Access",
                "sv": "EU:s kuratorspolicy kräver att publikationsartiklar måste vara öppen tillgång",
                "de": "Die EU-Kuratorenrichtlinie verlangt, dass Publikationsartikel Open Access sein müssen",
            },
            "level": "error",
            "condition": {
                "type": "comparison",
                "left": {"type": "field", "path": "metadata.resource_type.id"},
                "operator": "==",
                "right": "publication-article",
            },
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "access.files"},
                    "operator": "==",
                    "right": "public",
                }
            ],
        },
        {
            "id": "language:required",
            "title": {
                "en": "Language Required",
                "sv": "Språk krävs",
                "de": "Sprache erforderlich",
            },
            "message": {
                "en": "All records must specify a language",
                "sv": "Alla poster måste ange ett språk",
                "de": "Alle Datensätze müssen eine Sprache angeben",
            },
            "description": {
                "en": "Community guidelines require all records to have a language specified",
                "sv": "Gemenskapsriktlinjer kräver att alla poster har ett specificerat språk",
                "de": "Community-Richtlinien erfordern, dass alle Datensätze eine Sprache angeben",
            },
            "level": "warning",
            "checks": [{"type": "field", "path": "metadata.languages"}],
        },
        {
            "id": "mixed_example",
            "title": "Mixed Example (Backward Compatible)",
            "message": {
                "en": "This shows backward compatibility with mixed string/dict",
                "sv": "Detta visar bakåtkompatibilitet med blandad sträng/dict",
            },
            "description": "Simple string description still works",
            "level": "info",
            "checks": [{"type": "field", "path": "metadata.title"}],
        },
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
