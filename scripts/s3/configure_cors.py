"""Configure browser uploads for a local RustFS bucket (development only)."""

import argparse
import os

import botocore.session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="default")
    parser.add_argument(
        "--endpoint", default=os.environ.get("INVENIO_S3_ENDPOINT_URL", "http://localhost:9000")
    )
    parser.add_argument(
        "--origin", action="append",
        help="Allowed browser origin; repeat for multiple origins.",
    )
    args = parser.parse_args()
    origins = args.origin or [
        "https://127.0.0.1:5000", "https://localhost:5000",
        "https://127.0.0.1", "https://localhost",
    ]
    client = botocore.session.get_session().create_client(
        "s3",
        endpoint_url=args.endpoint,
        region_name=os.environ.get("INVENIO_S3_REGION_NAME", "us-east-1"),
        aws_access_key_id=os.environ.get("INVENIO_S3_ACCESS_KEY_ID", "CHANGE_ME"),
        aws_secret_access_key=os.environ.get("INVENIO_S3_SECRET_ACCESS_KEY", "CHANGE_ME"),
    )
    client.put_bucket_cors(
        Bucket=args.bucket,
        CORSConfiguration={"CORSRules": [{
            "AllowedOrigins": origins,
            "AllowedMethods": ["GET", "HEAD", "PUT", "POST", "DELETE"],
            "AllowedHeaders": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3600,
        }]},
    )
    print(f"Configured CORS for {args.bucket} at {args.endpoint}: {', '.join(origins)}")


if __name__ == "__main__":
    main()
