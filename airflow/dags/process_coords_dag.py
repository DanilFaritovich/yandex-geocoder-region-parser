import json
from typing import Any

from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sdk import Asset, AssetAlias, dag, task

from backend.api.key_pool import ApiKeyPool
from backend.bootstrap import create_etl_service

POINTS_ASSET_ALIAS = AssetAlias("geocoding-points")
REQUESTS_ASSET_ALIAS = AssetAlias("geocoding-requests")


@dag(
    dag_id="geocoding_requests",
    schedule=POINTS_ASSET_ALIAS,
    catchup=False,
    fail_fast=True,
    max_active_runs=1,
)
def geocoding_requests() -> None:

    @task(
        inlets=[POINTS_ASSET_ALIAS],
        multiple_outputs=True,
    )
    def get_job_metadata(*, inlet_events: dict[str, list[Any]]) -> dict:
        event = inlet_events[POINTS_ASSET_ALIAS][-1]

        return {
            "job_id": event.extra["job_id"],
            "place_id": event.extra["place_id"],
            "date": event.extra["date"],
            "requests_limit": event.extra["requests_limit"],
            "points_uri": event.asset.uri,
        }

    @task(inlets=[POINTS_ASSET_ALIAS])
    def get_point_keys(
        requests_limit: int, *, inlet_events: dict[str, list[Any]]
    ) -> list[str]:
        event = inlet_events[POINTS_ASSET_ALIAS][-1]

        points_uri = event.asset.uri

        bucket_name, points_key = S3Hook.parse_s3_url(points_uri)

        hook = S3Hook(
            aws_conn_id="minio_s3",
        )

        point_keys = (
            hook.list_keys(
                bucket_name=bucket_name,
                prefix=points_key,
            )
            or []
        )

        requests_prefix = points_key.replace(
            "points",
            "requests",
        )

        request_keys = (
            hook.list_keys(
                bucket_name=bucket_name,
                prefix=requests_prefix,
            )
            or []
        )

        processed_point_keys = {
            key.replace("requests", "points") for key in request_keys
        }

        unprocessed_point_keys = [
            key for key in point_keys if key not in processed_point_keys
        ]

        if not unprocessed_point_keys:
            return []

        key_capacity = ApiKeyPool.from_env().current_key_capacity()
        if key_capacity == 0:
            raise ValueError("All Yandex Geocoder API keys are exhausted or disabled")

        batch_size = min(requests_limit, key_capacity)

        return sorted(unprocessed_point_keys)[:batch_size]

    @task(
        pool="yandex_geocoder",
        retries=3,
    )
    def process_point(
        point_key: str,
        place_id: int,
    ) -> None:
        hook = S3Hook(
            aws_conn_id="minio_s3",
        )

        point_json = hook.read_key(
            key=point_key,
            bucket_name="geocoding",
        )

        point = json.loads(point_json)

        service = create_etl_service()

        request = service.process_point(
            place_id=place_id,
            longitude=point["longitude"],
            latitude=point["latitude"],
        )

        request_key = point_key.replace(
            "/points/",
            "/requests/",
        )

        request_data = [result.model_dump(mode="json") for result in request]

        hook.load_string(
            string_data=json.dumps(request_data),
            bucket_name="geocoding",
            key=request_key,
            replace=True,
        )

    @task(
        inlets=[POINTS_ASSET_ALIAS],
        outlets=[POINTS_ASSET_ALIAS, REQUESTS_ASSET_ALIAS],
    )
    def finalize_requests(
        *,
        inlet_events: dict[str, list[Any]],
        outlet_events: dict[str, Any],
    ) -> None:
        event = inlet_events[POINTS_ASSET_ALIAS][-1]

        job_id = event.extra["job_id"]
        place_id = event.extra["place_id"]
        date = event.extra["date"]

        points_uri = event.asset.uri
        bucket_name, points_prefix = S3Hook.parse_s3_url(points_uri)

        hook = S3Hook(aws_conn_id="minio_s3")
        point_keys = (
            hook.list_keys(
                bucket_name=bucket_name,
                prefix=points_prefix,
            )
            or []
        )

        requests_prefix = points_prefix.replace("points", "requests")
        request_keys = (
            hook.list_keys(
                bucket_name=bucket_name,
                prefix=requests_prefix,
            )
            or []
        )

        processed_point_keys = {
            key.replace("/requests/", "/points/") for key in request_keys
        }
        remaining = [key for key in point_keys if key not in processed_point_keys]

        if remaining:
            if not ApiKeyPool.from_env().has_available_key():
                raise ValueError(
                    "API keys are exhausted with "
                    f"{len(remaining)} points still unprocessed"
                )

            outlet_events[POINTS_ASSET_ALIAS].add(
                Asset(points_uri),
                extra={
                    "job_id": job_id,
                    "place_id": place_id,
                    "date": date,
                    "requests_limit": event.extra["requests_limit"],
                },
            )
            return

        requests_uri = f"s3://geocoding/{requests_prefix}"

        outlet_events[REQUESTS_ASSET_ALIAS].add(
            Asset(requests_uri),
            extra={
                "job_id": job_id,
                "place_id": place_id,
                "date": date,
            },
        )

    job = get_job_metadata()

    point_keys = get_point_keys(
        requests_limit=job["requests_limit"],
    )

    process_tasks = process_point.partial(
        place_id=job["place_id"],
    ).expand(
        point_key=point_keys,
    )

    process_tasks >> finalize_requests()


geocoding_requests()
