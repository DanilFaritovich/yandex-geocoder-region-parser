import json
from uuid import uuid4

from shapely import Polygon
import shapely

from backend.bootstrap import create_etl_service
from backend.etl.models import PointData

from airflow.sdk import AssetAlias, Asset, Param, dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from datetime import datetime, timezone

POLYGONS_ASSET_ALIAS = AssetAlias("geocoding-polygons")
POINTS_ASSET_ALIAS = AssetAlias("geocoding-points")


@dag(
    dag_id="geocoding_points",
    schedule=POLYGONS_ASSET_ALIAS,
    catchup=False,
)
def prepare_points():

    @task(
        inlets=[POLYGONS_ASSET_ALIAS],
        outlets=[POINTS_ASSET_ALIAS],
    )
    def generate_points(*, inlet_events, outlet_events):

        events = inlet_events[POLYGONS_ASSET_ALIAS]

        event = events[-1]

        job_id = event.extra["job_id"]
        place_id = event.extra["place_id"]
        date = event.extra["date"]
        distance_meters = event.extra["distance_meters"]

        polygon_uri = event.asset.uri
        bucket_name, polygon_key = S3Hook.parse_s3_url(
            polygon_uri
        )

        hook = S3Hook(
            aws_conn_id="minio_s3",
        )

        polygon_json = hook.read_key(
            key=polygon_key,
            bucket_name=bucket_name,
        )

        polygon = shapely.from_geojson(polygon_json)

        service = create_etl_service()

        points = service.generate_points(
            place_id=place_id,
            polygon=polygon,
            distance_meters=distance_meters,
        )

        for num, point in enumerate(points):
            point_key = (
                f"jobs/{date}/{job_id}/points/{num:06d}.json"
            )

            hook.load_string(
                string_data=json.dumps(point),
                bucket_name="geocoding",
                key=point_key,
                replace=True,
            )

        points_key = f"jobs/{date}/{job_id}/points/"
        points_uri = f"s3://geocoding/{points_key}"

        outlet_events[POINTS_ASSET_ALIAS].add(
            Asset(points_uri),
            extra={
                "job_id": job_id,
                "place_id": place_id,
                "date": date,
            },
        )

    generate_points()


prepare_points()