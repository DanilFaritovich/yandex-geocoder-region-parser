from dags.prepare_coords_dag import prepare_points
from dags.prepare_polygon_dag import prepare_polygon
from dags.process_coords_dag import geocoding_requests
from dags.save_processed_coords_dag import geocoding_save


def test_all_dags_can_be_created():
    dags = [
        prepare_polygon(),
        prepare_points(),
        geocoding_requests(),
        geocoding_save(),
    ]

    assert len(dags) == 4

    assert {dag.dag_id for dag in dags} == {
        "geocoding_polygon",
        "geocoding_points",
        "geocoding_requests",
        "geocoding_save",
    }
