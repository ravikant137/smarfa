import requests, time

base = 'http://127.0.0.1:8000'
print('pinging', base)

for p in [
    {'crop_id':'field-1','type':'growth','height_cm':10.0,'soil_moisture':45.0,'temperature_c':26.0},
    {'crop_id':'field-1','type':'growth','height_cm':10.1,'soil_moisture':26.0,'temperature_c':14.0},
    {'crop_id':'field-1','type':'intrusion','motion':True},
]:
    r = requests.post(base + '/sensor_data', json=p)
    print('POST', p['type'], r.status_code, r.text)
    time.sleep(0.2)

r = requests.get(base + '/alerts')
print('GET /alerts', r.status_code, r.json())

r = requests.post(base + '/mobile/register', json={'farmer_id': 'farmer-1', 'device_token': 'abc123'})
print('POST /mobile/register', r.status_code, r.json())

r = requests.get(base + '/mobile/devices')
print('GET /mobile/devices', r.status_code, r.json())

r = requests.post(base + '/mobile/send_push', json={'farmer_id': 'farmer-1', 'title': 'Test', 'body': 'Test push from script'})
print('POST /mobile/send_push', r.status_code, r.json())
