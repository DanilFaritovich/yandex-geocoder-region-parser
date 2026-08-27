import json

from backend.bootstrap import create_etl_service

from airflow.sdk import AssetAlias, dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from backend.transformer.models import GeocodeResult


REQUESTS_ASSET_ALIAS = AssetAlias("geocoding-requests")


@dag(
    dag_id="geocoding_save",
    schedule=REQUESTS_ASSET_ALIAS,
    catchup=False,
)
def geocoding_save():

    @task(
        inlets=[REQUESTS_ASSET_ALIAS]
    )
    def save_to_csv(*, inlet_events):
        event = inlet_events[REQUESTS_ASSET_ALIAS][-1]

        job_id = event.extra["job_id"]
        date = event.extra["date"]

        requests_uri = event.asset.uri

        bucket_name, requests_prefix = S3Hook.parse_s3_url(
            requests_uri
        )

        hook = S3Hook(
            aws_conn_id="minio_s3",
        )

        request_keys = hook.list_keys(
            bucket_name=bucket_name,
            prefix=requests_prefix,
        )

        if not request_keys:
            raise ValueError(
                f"No requests found in {requests_uri}"
            )

        service = create_etl_service()

        for request_key in sorted(request_keys):
            request_json = hook.read_key(
                key=request_key,
                bucket_name=bucket_name,
            )

            requests_data = json.loads(request_json)

            requests = [
                GeocodeResult.model_validate(result)
                for result in requests_data
            ]

            service.save(requests)

        result_key = (
            f"jobs/{date}/{job_id}/"
            f"result/districts.csv"
        )

        hook.load_file(
            filename="/opt/airflow/data/districts.csv",
            bucket_name=bucket_name,
            key=result_key,
            replace=True,
        )


    save_to_csv()


geocoding_save()