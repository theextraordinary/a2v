import requests


def call_edge(audio_path, edge_url):
    with open(audio_path, 'rb') as f:
        files = {'file': f}
        resp = requests.post(edge_url, files=files, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Edge error {resp.status_code}: {resp.text}')
    return resp.json()['segments']


def call_edge_words(audio_path, edge_url):
    with open(audio_path, 'rb') as f:
        files = {'file': f}
        resp = requests.post(edge_url, files=files, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Edge error {resp.status_code}: {resp.text}')
    return resp.json()['words']


def call_cloud(segments, cloud_url):
    resp = requests.post(cloud_url, json={'segments': segments}, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Cloud error {resp.status_code}: {resp.text}')
    return resp.json()['timeline']


def call_cloud_correct(text, cloud_url):
    resp = requests.post(cloud_url, json={'text': text}, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Cloud error {resp.status_code}: {resp.text}')
    return resp.json()['text']


def call_cloud_important(text, cloud_url):
    resp = requests.post(cloud_url, json={'text': text}, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Cloud error {resp.status_code}: {resp.text}')
    return resp.json()['words']


def call_cloud_edit_decisions(payload, cloud_url):
    resp = requests.post(cloud_url, json=payload, timeout=300)
    if not resp.ok:
        raise RuntimeError(f'Cloud error {resp.status_code}: {resp.text}')
    return resp.json()['decisions']
