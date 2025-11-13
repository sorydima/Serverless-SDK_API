from mesh.data_lake import MeshDataLake


def test_data_lake_ingest_and_count():
    lake = MeshDataLake(storage_path='.test_data_lake')
    lake.clear()
    lake.ingest({'type': 'traffic', 'value': 42})
    lake.ingest({'type': 'traffic', 'value': 7})
    lake.ingest({'type': 'environment', 'value': 3})
    counts = lake.count_by_type()
    assert counts['traffic'] == 2
    assert counts['environment'] == 1
