from celery import shared_task
from invenio_files_rest.models import FileInstance
from invenio_files_rest.tasks import remove_file_data


@shared_task(ignore_result=True)
def clear_orphaned_files(force_delete_check=lambda file_instance: True, limit=500):
    """Delete orphaned files from DB and storage.

    .. note::

        Orphan files are files
        (:class:`invenio_files_rest.models.FileInstance` objects and their
        on-disk counterparts) that do not have any
        :class:`invenio_files_rest.models.ObjectVersion` objects associated
        with them (anymore).

    The celery beat configuration for scheduling this task may set values for
    this task's parameters:

    .. code-block:: python

        "clear-orphan-files": {
            "task": "invenio_files_rest.tasks.clear_orphaned_files",
            "schedule": 60 * 60 * 24,
            "kwargs": {
                "force_delete_check": lambda file: False,
                "limit": 500,
            }
        }

    :param force_delete_check: A function to be called on each orphan file instance
    to check if its deletion should be forced (bypass the
    check of its ``writable`` flag).
    For example, this function can be used to force-delete
    files only if they are located on the local file system.
    Signature: The function should accept a
    :class:`invenio_files_rest.models.FileInstance` object
    and return a boolean value.
    Default: Never force-delete any orphan files
    (``lambda file_instance: False``).
    :param limit: Limit for the number of orphan files considered for deletion in each
        task execution (and thus the number of generated celery tasks).
        A value of zero (0) or lower disables the limit.
    """
    # with the tilde (~) operator, we get all file instances that *don't*
    # have any associated object versions
    query = FileInstance.query.filter(~FileInstance.objects.any())
    if limit > 0:
        query = query.limit(limit)

    for orphan in query:
        # note: the ID is cast to str because serialization of UUID objects can fail
        remove_file_data.delay(str(orphan.id), force=force_delete_check(orphan))
