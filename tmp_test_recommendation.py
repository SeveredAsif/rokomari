import json
import urllib.request
import urllib.parse


def request_json(url, method='GET', data=None, headers=None):
    headers = headers or {}
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
        headers = {**headers, 'Content-Type': 'application/json'}
    req = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

results = {}
status, health = request_json('http://localhost:8001/health')
results['health'] = {'status_code': status, 'body': health}

status, hello = request_json('http://localhost:8001/hello')
results['hello'] = {'status_code': status, 'body': hello}

status, popular1 = request_json('http://localhost:8001/recommendations/popular?limit=3')
status2, popular2 = request_json('http://localhost:8001/recommendations/popular?limit=3')
results['popular_first'] = {'status_code': status, 'source': popular1.get('source'), 'count': popular1.get('count', len(popular1.get('results', [])))}
results['popular_second'] = {'status_code': status2, 'source': popular2.get('source'), 'count': popular2.get('count', len(popular2.get('results', [])))}

status, login = request_json('http://localhost:8000/auth/login', method='POST', data={'email': 'user1@mail.com', 'password': 'password1'})
token = login['access_token']
headers = {'Authorization': f'Bearer {token}'}
results['login'] = {'status_code': status, 'token_type': login.get('token_type')}

q = urllib.parse.quote('Product 1')
status, search1 = request_json(f'http://localhost:8001/search?q={q}&threshold=0.05', headers=headers)
status2, search2 = request_json(f'http://localhost:8001/search?q={q}&threshold=0.05', headers=headers)
results['search_first'] = {'status_code': status, 'source': search1.get('source'), 'count': search1.get('count', len(search1.get('results', [])))}
results['search_second'] = {'status_code': status2, 'source': search2.get('source'), 'count': search2.get('count', len(search2.get('results', [])))}

status, rec1 = request_json('http://localhost:8001/recommendations?limit=5&threshold=0.05', headers=headers)
status2, rec2 = request_json('http://localhost:8001/recommendations?limit=5&threshold=0.05', headers=headers)
results['recommendations_first'] = {'status_code': status, 'source': rec1.get('source'), 'count': rec1.get('count', len(rec1.get('results', [])))}
results['recommendations_second'] = {'status_code': status2, 'source': rec2.get('source'), 'count': rec2.get('count', len(rec2.get('results', [])))}

print(json.dumps(results, indent=2))
