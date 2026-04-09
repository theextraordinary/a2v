import requests


def call_edge(audio_path, edge_url):
    with open(audio_path, 'rb') as f:
        files = {'file': f}
        resp = requests.post(edge_url, files=files, timeout=300)
    resp.raise_for_status()
    return resp.json()['segments']


def call_cloud(segments, cloud_url):
    resp = requests.post(cloud_url, json={'segments': segments}, timeout=300)
    resp.raise_for_status()
    return resp.json()['timeline']
