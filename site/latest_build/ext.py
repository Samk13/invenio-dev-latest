"""Application extension hooks."""

from __future__ import annotations

from .accounts import apply_user_roles_patch
from .accounts.routes import create_roles_blueprint


def _init_roles(app):
    """Apply shared role customisations."""
    apply_user_roles_patch(app)


def finalize_app(app):
    """Executed when the Invenio app initialises."""
    _init_roles(app)
    app.register_blueprint(
        create_roles_blueprint(
            name="latest_build_roles_ui",
            url_prefix="/api",
        )
    )


def api_finalize_app(app):
    """Executed when the Invenio API app initialises."""
    _init_roles(app)
    app.register_blueprint(create_roles_blueprint())
