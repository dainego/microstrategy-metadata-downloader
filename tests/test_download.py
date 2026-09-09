"""Pruebas sin servidor: ejemplos provistos y flujo HTTP simulado."""
import csv
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import config
import metadata
import service
from exporters import write_to_json, write_to_text

FIXTURES = Path(__file__).parent / 'fixtures'


def fixture(t):
    return json.loads((FIXTURES / f'{t}.json').read_text())


class Response:
    def __init__(self, data):
        self.data, self.closed = data, False
    def json(self):
        return self.data
    def close(self):
        self.closed = True


class DownloadTests(unittest.TestCase):
    def test_examples(self):
        for t, count in [(12, 3), (4, 1), (1, 1), (13, 6)]:
            d = fixture(t)
            settings = config.OBJECT_TYPES[t]
            rows = metadata.flatten_object_details([d],
                {d['information']['objectId']: settings['folder_prefix'] + '/Modelo/Submodelo'},
                t, settings['folder_prefix'])
            self.assertEqual(len(rows), count)
            self.assertEqual(rows[0]['model'], 'Modelo')
            self.assertEqual(rows[0]['submodel'], 'Submodelo')
            if t == 1:
                self.assertEqual(rows[0]['predicateName'], 'Tipo de Comprobante')
                self.assertEqual(rows[0]['elementId'], 'h5')
            if t == 4:
                self.assertEqual(rows[0]['filterName'], 'Max Fecha Suscripcion')

    def test_empty_fields_and_nested_filter(self):
        for t in config.OBJECT_TYPES:
            rows = metadata.flatten_object_details([None, {'information': {'objectId': 'X'}}], {}, t, '')
            self.assertEqual(len(rows), 1)
        d = fixture(1)
        node = d['qualification']['tree']
        d['qualification']['tree'] = {'type': 'operator', 'children': [node, node]}
        rows = metadata.flatten_object_details([d], {}, 1, '')
        self.assertEqual(len(rows), 2)

    def test_export_roundtrip_and_empty(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'result.txt'
            write_to_text([{'name': 'A|B', 'description': 'Una\n línea "citada"'}], path)
            with path.open(newline='') as f:
                rows = list(csv.DictReader(f, delimiter='|'))
            self.assertEqual(rows[0]['name'], 'A|B')
            self.assertEqual(rows[0]['description'], 'Una línea "citada"')
            write_to_text([], path, fieldnames=['name'])
            self.assertEqual(path.read_text(), 'name\n')
            write_to_json([], path)
            self.assertEqual(json.loads(path.read_text()), [])

    def test_full_service_success_partial_empty_and_failure(self):
        for t in config.OBJECT_TYPES:
            for mode in ['success', 'partial', 'empty', 'failed']:
                detail = fixture(t)
                oid = detail['information']['objectId']
                replies, clients = [], []
                class Client:
                    def __init__(self, *args):
                        self.logger = logging.getLogger('test')
                        self.logged_out = self.closed = False
                        clients.append(self)
                    def login(self, *args): pass
                    def logout(self):
                        self.logged_out = True
                        return True
                    def close(self): self.closed = True
                    def api_call(self, method, endpoint, **kw):
                        if method == 'POST':
                            assert kw['params']['type'] == t
                            data = {'id': 'search'}
                        elif endpoint.endswith('/tree'):
                            data = {'children': [{'name': 'Modelo', 'children': [{'id': oid}]}]}
                        elif endpoint == '/metadataSearches/results':
                            data = [] if mode == 'empty' else [{'id': oid}]
                            if mode == 'partial': data.append({'id': 'bad'})
                        else:
                            assert endpoint.startswith(config.OBJECT_TYPES[t]['endpoint'].split('{')[0])
                            if mode == 'failed' or endpoint.endswith('/bad'): return None
                            data = detail
                        response = Response(data)
                        replies.append(response)
                        return response
                with tempfile.TemporaryDirectory() as folder, patch.multiple(config,
                        BASE_URL='https://example.test/api', ACCOUNT_ID='test', ACCOUNT_PASSWORD='test',
                        RESULTS_FOLDER=Path(folder)), patch.dict(config.PROJECTS,
                        {'test': {'name':'Test', 'project_id':'P', config.OBJECT_TYPES[t]['root_key']:'root'}}), \
                        patch.object(service, 'MicroStrategyClient', Client):
                    if mode == 'failed':
                        with self.assertRaises(RuntimeError):
                            service.download_metadata('test', t, logging.getLogger('test'))
                    else:
                        result = service.download_metadata('test', t, logging.getLogger('test'))
                        self.assertEqual(result['objects_downloaded'], 0 if mode == 'empty' else 1)
                        self.assertEqual(result['objects_failed'], 1 if mode == 'partial' else 0)
                        self.assertEqual(result['status'], 'completed_with_warnings' if mode == 'partial' else 'completed')
                        for path in result['files'].values(): self.assertTrue(Path(path).exists())
                self.assertTrue(clients[0].closed and clients[0].logged_out)
                self.assertTrue(all(r.closed for r in replies))

    def test_api(self):
        import api
        from fastapi.testclient import TestClient
        api.jobs.clear()
        with TestClient(api.app) as client:
            self.assertEqual(client.post('/jobs', json={'project_key':'1','object_type':99}).status_code, 422)
            self.assertEqual(client.post('/jobs', json={'project_key':'1','object_type':True}).status_code, 422)
            with patch.object(api, 'download_metadata', side_effect=RuntimeError('test')) as download:
                response = client.post('/jobs', json={'project_key':'1','object_type':12})
                self.assertEqual(response.status_code, 202)
                download.assert_called_once_with('1',12)
                job = client.get('/jobs/'+response.json()['job_id']).json()
                self.assertEqual(job['object_type'],12)
                self.assertEqual(job['status'],'failed')
        api.jobs.clear()


if __name__ == '__main__':
    unittest.main()
