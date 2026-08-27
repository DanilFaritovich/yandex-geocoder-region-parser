from dags.save_processed_coords_dag import geocoding_save


def test_geocoding_save_dag():
    dag = geocoding_save()

    assert dag.dag_id == "geocoding_save"
    assert dag.catchup is False

    assert set(dag.task_ids) == {
        "save_to_csv",
    }


def test_save_to_csv_task():
    dag = geocoding_save()

    task = dag.get_task("save_to_csv")

    assert task is not None
    assert len(task.inlets) == 1