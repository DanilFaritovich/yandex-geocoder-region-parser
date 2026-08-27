from dags.prepare_polygon_dag import prepare_polygon


def test_prepare_polygon_dag():
    dag = prepare_polygon()

    assert dag.dag_id == "geocoding_polygon"
    assert dag.schedule is None
    assert dag.catchup is False

    assert set(dag.task_ids) == {
        "generate_polygon",
    }


def test_generate_polygon_task():
    dag = prepare_polygon()

    task = dag.get_task("generate_polygon")

    assert task is not None
    assert len(task.outlets) == 1