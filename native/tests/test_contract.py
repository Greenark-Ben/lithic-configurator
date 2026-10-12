import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'public/native'))
from contract import BUILDER, expected_parts, validate, verification_sizes, volume_mm3

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((Path(__file__).resolve().parents[2] / 'public/native/afkc-source.json').read_text())
        self.request = {'kind':'lithic-build-request','schemaVersion':'0.1','units':'mm','geometryEngine':'fixed-window-profile-sweeps/0.1','approvedAt':'2026-10-12',
                        'definition':{'id':'elitfonster-afkc-profile-proof','operation':'fixed','frameFace':53.5,'frameDepth':105,'glazingThickness':48,'profile':{'id':'afkc-polygon/0.1','manufacturerApproved':False,'source':self.source}},
                        'configuration':{'width':1200,'height':1500,'interior':'timber','exterior':'graphite'},'parts':expected_parts(self.source,1200,1500)}
    def check(self, request):
        raw = json.dumps(request).encode()
        return validate(raw, {'builder':BUILDER,'requestSha256':hashlib.sha256(raw).hexdigest()}, self.source)
    def test_rejects_geometry_and_source_mutation(self):
        for change in ['geometry', 'source', 'section', 'finish', 'nan', 'bool']:
            request = copy.deepcopy(self.request)
            if change == 'geometry': request['parts'][0]['sweep']['lengthMm'] += 1
            if change == 'source': request['definition']['profile']['source']['profiles']['timberHead']['pointsMm'][0][0] = 10
            if change == 'section': request['definition']['frameFace'] = 54
            if change == 'finish': request['configuration']['interior'] = 'steel'
            if change == 'nan': request['configuration']['width'] = float('nan')
            if change == 'bool': request['configuration']['width'] = True
            with self.subTest(change=change):
                with self.assertRaises(ValueError): self.check(request)
    def test_digest_is_checked(self):
        with self.assertRaises(ValueError): validate(json.dumps(self.request).encode(), {'builder':BUILDER,'requestSha256':'0'*64}, self.source)
    def test_size_cases_are_unique(self):
        self.assertEqual(len(verification_sizes(self.request)), 3)
        self.request['configuration']['width'] = 1275
        self.assertEqual(len(verification_sizes(self.request)), 4)
    def test_reproduces_prior_native_proof_volumes(self):
        parts = self.request['parts']
        self.assertAlmostEqual(sum(volume_mm3(p) for p in parts if p['role']=='timber'),25646267.25)
        self.assertAlmostEqual(sum(volume_mm3(p) for p in parts if p['role']=='aluminium'),647988.25)

if __name__ == '__main__': unittest.main()
