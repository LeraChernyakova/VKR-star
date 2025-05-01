import time
import requests
import statistics
import json
import os

API_KEY = "lyjwakywqahzzjvj"

# Получаем папку со скриптом
BASE_DIR = os.path.dirname(__file__)
images = [
    os.path.join(BASE_DIR, f"test{idx}.png")
    for idx in [1,2,3,4,5,7,8,10]
]

headers = {'User-Agent': 'AstrometryTimingScript/1.0'}

def login():
    """Логинимся и возвращаем session-токен."""
    payload = {'request-json': json.dumps({'apikey': API_KEY})}
    r = requests.post("https://nova.astrometry.net/api/login",
                      data=payload, headers=headers)
    r.raise_for_status()
    resp = r.json()
    if resp.get('status') != 'success' or 'session' not in resp:
        raise RuntimeError(f"Login failed: {resp}")
    return resp['session']

def submit_image(filepath, session):
    """Загружаем файл, возвращаем subid."""
    with open(filepath, 'rb') as f:
        files = {'file': f}
        data = {'request-json': json.dumps({'session': session})}
        r = requests.post("https://nova.astrometry.net/api/upload",
                          files=files, data=data, headers=headers)
    r.raise_for_status()
    resp = r.json()
    if resp.get('status') != 'success' or 'subid' not in resp:
        raise RuntimeError(f"Upload failed: {resp}")
    return resp['subid']

def wait_for_job(subid):
    while True:
        r = requests.get(f"https://nova.astrometry.net/api/submissions/{subid}",
                         headers=headers)
        r.raise_for_status()
        jobs = r.json().get('jobs')
        if jobs:
            return jobs[0]
        time.sleep(1)


def wait_for_solve(job_id):
    url = f"https://nova.astrometry.net/api/jobs/{job_id}/info/"
    while True:
        r = requests.get(url, headers=headers)

        # 1) Сначала убедимся, что статус 200 OK
        try:
            r.raise_for_status()
        except Exception as e:
            print(f"HTTP error {r.status_code} при запросе {url}:")
            print(r.text[:200])
            time.sleep(2)
            continue

        # 2) Попробуем распарсить JSON
        try:
            j = r.json()
        except JSONDecodeError:
            print("Ожидался JSON, получил:")
            print(r.text[:200])
            time.sleep(2)
            continue

        # 3) Теперь безопасно читаем статус
        status = j.get('status')
        if status == 'solved':
            return
        if status in ('failure', 'error'):
            raise RuntimeError(f"Job {job_id} завершился с ошибкой: {j}")

        # Если всё ещё в процессе, ждём и повторяем
        time.sleep(2)

if __name__ == "__main__":
    session = login()
    times = []
    for img in images:
        print(f"Обработка {img}…")
        t0 = time.time()
        subid = submit_image(img, session)
        job_id = wait_for_job(subid)
        wait_for_solve(job_id)
        dt = time.time() - t0
        times.append(dt)
        print(f"  Готово за {dt:.2f} сек")
    print(f"\nСреднее время обработки: {statistics.mean(times):.2f} сек")
