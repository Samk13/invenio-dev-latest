"""Script to update file URIs in the database from OLD_PREFIX to NEW_PREFIX for migration."""
from invenio_db import db
from invenio_files_rest.models import FileInstance

OLD_PREFIX = "s3://test-01/"
NEW_PREFIX = "s3://test-02/"

count = 0
for f in FileInstance.query.filter(FileInstance.uri.startswith(OLD_PREFIX)):
    # uri example:
    # s3://default/00/1c/866d-3e78-40b3-bf4d-edb1980c8526/data
    f.uri = f.uri.replace(OLD_PREFIX, NEW_PREFIX, 1)
    count += 1

db.session.commit()
print(f"Updated {count} file URIs")

# Make sure to update the default location to point to the new S3 bucket before running this script.
# S3_LOCATION="s3://test-02"
# invenio files location create --default 'test-02-location' "$S3_LOCATION"
