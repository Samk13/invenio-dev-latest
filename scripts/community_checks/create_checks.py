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

COMMUNITY_SLUG = "test-comm"
# Deliberately broad ruleset for testing feedback rendering across deposit fields.
RIGHTS_RULES = {
    "rules": [
        {
            "id": "resource-type:test-publication",
            "title": {
                "en": "Resource type test",
                "sv": "Test av resurstyp",
                "de": "Ressourcentyp-Test",
            },
            "message": {
                "en": "Test info: resource type should be a publication article",
                "sv": "Testinfo: resurstypen ska vara en publikationsartikel",
                "de": "Testinfo: Ressourcentyp soll ein Publikationsartikel sein",
            },
            "description": {
                "en": "Use this rule to verify info feedback on the resource type field.",
                "sv": "Använd denna regel för att verifiera infofeedback på resurstypfältet.",
                "de": "Diese Regel prüft Info-Feedback am Ressourcentyp-Feld.",
            },
            "level": "info",
            "error_path": "metadata.resource_type",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.resource_type.id"},
                    "operator": "==",
                    "right": "publication-article",
                }
            ],
        },
        {
            "id": "title:min-length",
            "title": {
                "en": "Title length test",
                "sv": "Test av titellängd",
                "de": "Titellängen-Test",
            },
            "message": {
                "en": "Test warning: title should be at least 10 characters",
                "sv": "Testvarning: titeln bör vara minst 10 tecken",
                "de": "Testwarnung: Titel soll mindestens 10 Zeichen haben",
            },
            "description": {
                "en": "Use a short title to verify warning feedback on the title field.",
                "sv": "Använd en kort titel för att verifiera varningsfeedback på titelfältet.",
                "de": "Ein kurzer Titel löst Warn-Feedback am Titelfeld aus.",
            },
            "level": "warning",
            "error_path": "metadata.title",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.title"},
                    "operator": "min",
                    "right": 10,
                }
            ],
        },
        {
            "id": "creators:not-sam",
            "title": {
                "en": "Creator name test",
                "sv": "Test av skaparnamn",
                "de": "Erstellername-Test",
            },
            "message": {
                "en": "Test error: creator name must not be sam",
                "sv": "Testfel: skaparnamnet får inte vara sam",
                "de": "Testfehler: Erstellername darf nicht sam sein",
            },
            "description": {
                "en": "Set a creator name to sam to verify error feedback on creators.",
                "sv": "Sätt ett skaparnamn till sam för att verifiera felfeedback på skapare.",
                "de": "Setze einen Erstellernamen auf sam, um Fehlerfeedback zu prüfen.",
            },
            "level": "error",
            "error_path": "metadata.creators",
            "checks": [
                {
                    "type": "list",
                    "operator": "all",
                    "path": "metadata.creators",
                    "predicate": {
                        "type": "comparison",
                        "left": {"type": "field", "path": "person_or_org.name"},
                        "operator": "!=",
                        "right": "sam",
                    },
                }
            ],
        },
        {
            "id": "publisher:not-latest-build",
            "title": {
                "en": "Publisher test",
                "sv": "Test av utgivare",
                "de": "Herausgeber-Test",
            },
            "message": {
                "en": "Test info: publisher should not be latest-build",
                "sv": "Testinfo: utgivaren bör inte vara latest-build",
                "de": "Testinfo: Herausgeber soll nicht latest-build sein",
            },
            "description": {
                "en": "The example draft uses latest-build, so this should show info feedback.",
                "sv": "Exempelutkastet använder latest-build, så detta bör visa infofeedback.",
                "de": "Der Beispielentwurf nutzt latest-build und zeigt daher Info-Feedback.",
            },
            "level": "info",
            "error_path": "metadata.publisher",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.publisher"},
                    "operator": "!=",
                    "right": "latest-build",
                }
            ],
        },
        {
            "id": "publication-date:not-example-date",
            "title": {
                "en": "Publication date test",
                "sv": "Test av publiceringsdatum",
                "de": "Publikationsdatum-Test",
            },
            "message": {
                "en": "Test warning: publication date should not be 2026-06-29",
                "sv": "Testvarning: publiceringsdatum bör inte vara 2026-06-29",
                "de": "Testwarnung: Publikationsdatum soll nicht 2026-06-29 sein",
            },
            "description": {
                "en": "The example draft uses this date, so this verifies date-field feedback.",
                "sv": "Exempelutkastet använder detta datum, så detta verifierar datumfeedback.",
                "de": "Der Beispielentwurf nutzt dieses Datum und prüft Datumsfeedback.",
            },
            "level": "warning",
            "error_path": "metadata.publication_date",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.publication_date"},
                    "operator": "!=",
                    "right": "2026-06-29",
                }
            ],
        },
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
            "error_path": "metadata.rights",
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
            "error_path": "access.files",
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
            "id": "access-files:test-restricted",
            "title": {
                "en": "File access test",
                "sv": "Test av filåtkomst",
                "de": "Dateizugriff-Test",
            },
            "message": {
                "en": "Test warning: file access should be restricted",
                "sv": "Testvarning: filåtkomst bör vara begränsad",
                "de": "Testwarnung: Dateizugriff soll eingeschränkt sein",
            },
            "description": {
                "en": "The example draft has public files, so this verifies access feedback.",
                "sv": "Exempelutkastet har offentliga filer, så detta verifierar åtkomstfeedback.",
                "de": "Der Beispielentwurf hat öffentliche Dateien und prüft Zugriffsfeedback.",
            },
            "level": "warning",
            "error_path": "access.files",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "access.files"},
                    "operator": "==",
                    "right": "restricted",
                }
            ],
        },
        {
            "id": "access-record:test-restricted",
            "title": {
                "en": "Record access test",
                "sv": "Test av poståtkomst",
                "de": "Datensatzzugriff-Test",
            },
            "message": {
                "en": "Test info: record access should be restricted",
                "sv": "Testinfo: poståtkomst bör vara begränsad",
                "de": "Testinfo: Datensatzzugriff soll eingeschränkt sein",
            },
            "description": {
                "en": "The example draft is public, so this verifies record access feedback.",
                "sv": "Exempelutkastet är offentligt, så detta verifierar poståtkomstfeedback.",
                "de": "Der Beispielentwurf ist öffentlich und prüft Datensatzzugriff.",
            },
            "level": "info",
            "error_path": "access.record",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "access.record"},
                    "operator": "==",
                    "right": "restricted",
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
            "error_path": "metadata.languages",
            "checks": [{"type": "field", "path": "metadata.languages"}],
        },
        {
            "id": "description:min-length",
            "title": {
                "en": "Description minimum length",
                "sv": "Minsta längd för beskrivning",
                "de": "Mindestlänge der Beschreibung",
            },
            "message": {
                "en": "The record description must be at least 10 characters",
                "sv": "Postens beskrivning måste vara minst 10 tecken",
                "de": "Die Beschreibung des Datensatzes muss mindestens 10 Zeichen lang sein",
            },
            "description": {
                "en": "Community guidelines require a short descriptive summary for each record.",
                "sv": "Gemenskapsriktlinjer kräver en kort beskrivande sammanfattning för varje post.",
                "de": "Community-Richtlinien verlangen eine kurze beschreibende Zusammenfassung für jeden Datensatz.",
            },
            "level": "warning",
            "error_path": "metadata.description",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.description"},
                    "operator": "min",
                    "right": 50,
                }
            ],
        },
        {
            "id": "mixed_example",
            "title": "Mixed Example (Backward Compatible)",
            "message": {
                "en": "This shows backward compatibility with mixed string/dict",
                "sv": "Detta visar bakåtkompatibilitet med blandad sträng/dict",
            },
            "description": "A string without being wrapped in a translatable dict still works as well",
            "level": "info",
            "error_path": "metadata.title",
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
