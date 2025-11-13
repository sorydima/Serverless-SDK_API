import asyncio
from ai.vibe.vibe import Vibe
from mesh.data_lake import MeshDataLake


def test_vibe_object():
    v = Vibe(level=0.7, tags={'mood': 'focused'})
    d = v.to_dict()
    assert 'level' in d and d['level'] == 0.7


def test_forward_includes_vibe():
    lake = MeshDataLake(storage_path='.test_data_lake')
    item = {'type': 'sensor_data', 'value': 1, 'vibe': {'level': 0.3, 'tags': {'a': 1}}}
    lake.ingest(item)
    counts = lake.count_by_type()
    assert counts.get('sensor_data', 0) == 1
