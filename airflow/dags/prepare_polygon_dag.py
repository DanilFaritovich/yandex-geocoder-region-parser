from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import shapely
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sdk import Asset, AssetAlias, Param, dag, task

from backend.bootstrap import create_etl_service

POLYGONS_ASSET_ALIAS = AssetAlias("geocoding-polygons")


@dag(
    dag_id="geocoding_polygon",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    render_template_as_native_obj=True,
    params={
        "place_id": Param(
            37592,
            type="integer",
            minimum=1,
        ),
        "distance_meters": Param(
            1000,
            type="integer",
            minimum=1,
        ),
    },
)
def prepare_polygon() -> None:

    @task(outlets=[POLYGONS_ASSET_ALIAS])
    def generate_polygon(
        place_id: int, distance_meters: int, *, outlet_events: dict[str, Any]
    ) -> None:
        service = create_etl_service()

        polygon = service.get_place_polygon(place_id=place_id)

        job_id = str(uuid4())
        job_date = datetime.now(UTC).date().isoformat()

        hook = S3Hook(
            aws_conn_id="minio_s3",
        )

        s3_key = f"jobs/{job_date}/{job_id}/polygon.json"

        polygon_json = shapely.to_geojson(polygon)

        hook.load_string(
            string_data=polygon_json,
            bucket_name="geocoding",
            key=s3_key,
            replace=True,
        )

        s3_uri = f"s3://geocoding/{s3_key}"

        outlet_events[POLYGONS_ASSET_ALIAS].add(
            Asset(s3_uri),
            extra={
                "job_id": job_id,
                "place_id": place_id,
                "date": job_date,
                "distance_meters": distance_meters,
            },
        )

    generate_polygon(
        place_id="{{ params.place_id }}",
        distance_meters="{{ params.distance_meters }}",
    )


prepare_polygon()
