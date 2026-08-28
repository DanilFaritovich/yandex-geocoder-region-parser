from dags.prepare_coords_dag import prepare_points


def test_prepare_points_dag():
    dag = prepare_points()

    assert dag.dag_id == "geocoding_points"
    assert dag.catchup is False

    assert set(dag.task_ids) == {
        "generate_points",
    }


def test_generate_points_task():
    dag = prepare_points()

    task = dag.get_task("generate_points")

    assert task is not None
    assert len(task.inlets) == 1
    assert len(task.outlets) == 1
