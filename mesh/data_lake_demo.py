"""Small demo script showing Mesh Data Lake ingestion and analysis.

Run programmatically or via pytest to ensure basic functionality.
"""
from mesh.data_lake import MeshDataLake


def run_demo():
    lake = MeshDataLake(storage_path='.demo_data_lake')
    lake.clear()
    # ingest sample stream
    lake.ingest({'type': 'traffic', 'value': 12})
    lake.ingest({'type': 'traffic', 'value': 7})
    lake.ingest({'type': 'environment', 'value': 3})
    counts = lake.count_by_type()
    path = lake.flush('demo_output.json')
    return counts, path


if __name__ == '__main__':
    print(run_demo())
