from dags.process_coords_dag import geocoding_requests


def test_geocoding_requests_dag():
    dag = geocoding_requests()

    assert dag.dag_id == "geocoding_requests"
    assert dag.catchup is False

    assert set(dag.task_ids) == {
        "get_job_metadata",
        "get_point_keys",
        "process_point",
        "finalize_requests",
    }


def test_get_job_metadata_task():
    dag = geocoding_requests()

    task = dag.get_task("get_job_metadata")

    assert task is not None
    assert len(task.inlets) == 1


def test_get_point_keys_task():
    dag = geocoding_requests()

    task = dag.get_task("get_point_keys")

    assert task is not None
    assert len(task.inlets) == 1


def test_process_point_task():
    dag = geocoding_requests()

    task = dag.get_task("process_point")

    assert task is not None
    assert task.pool == "yandex_geocoder"
    assert task.retries == 3


def test_finalize_requests_task():
    dag = geocoding_requests()

    task = dag.get_task("finalize_requests")

    assert task is not None
    assert len(task.inlets) == 1
    assert len(task.outlets) == 1
