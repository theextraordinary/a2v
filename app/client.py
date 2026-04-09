import requests


def call_edge(audio_path, edge_url):
    with open(audio_path, 'rb') as f:
        files = {'file': f}
        resp = requests.post(edge_url, files=files, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Edge error {resp.status_code}: {resp.text}')
    return resp.json()['segments']


def call_cloud(segments, cloud_url):
    resp = requests.post(cloud_url, json={'segments': segments}, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Cloud error {resp.status_code}: {resp.text}')
    return resp.json()['timeline']
