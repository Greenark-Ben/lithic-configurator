import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'public/native'))
from contract import BUILDER, expected_parts, validate, verification_sizes, volume_mm3, native_specs

class ContractTests(unittest.TestCase):
    def test_accepted_native_source_is_unchanged(self):
        root = Path(__file__).resolve().parents[2]
        evidence = json.loads((root / 'docs/evidence/afkc-shared-parameters-0.2.2.json').read_text())
        self.assertEqual(evidence['builder'], BUILDER)
        self.assertFalse(evidence['nativeParameterFlex'])
        self.assertFalse(evidence['manufacturerApproved'])
        for name in ['script.py', 'authoring.py', 'contract.py', 'drawings.py', 'afkc-source.json']:
            with self.subTest(name=name):
                raw = (root / 'public/native' / name).read_bytes().replace(b'\r\n', b'\n')
                # The accepted Windows package contains both LF and CRLF files.
                # Allow checkout line-ending conversion, but no source edits.
                hashes = [hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b'\n', b'\r\n')).hexdigest()]
                self.assertIn(evidence['packageHashes'][name], hashes,
                                 'Native source changed: require new Revit evidence before updating the accepted baseline')
    def setUp(self):
        self.source = json.loads((Path(__file__).resolve().parents[2] / 'public/native/afkc-source.json').read_text())
        self.request = {'kind':'lithic-build-request','schemaVersion':'0.1','units':'mm','geometryEngine':'fixed-window-profile-sweeps/0.2.2','approvedAt':'2026-10-12',
                        'definition':{'id':'elitfonster-afkc-profile-proof','operation':'fixed','frameFace':53.5,'frameDepth':105,'glazingThickness':48,'profile':{'id':'afkc-polygon/0.2.2','manufacturerApproved':False,'source':self.source}},
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
    def test_reviewed_glazing_and_native_join_envelope(self):
        parts=self.request['parts']
        panes=[p for p in parts if p['role']=='glazing']
        self.assertEqual([p['size'][2] for p in panes],[4,4,4])
        self.assertEqual([p['position'][2] for p in panes],[-8.5,13.5,35.5])
        self.assertEqual(len([p for p in parts if p['role']=='spacer']),8)
        self.assertEqual(len([p for p in parts if p['role']=='seal']),4)
        native=native_specs(self.source,1200,1500)
        self.assertEqual(len(native),22)
        joined=next(p for p in native if p['id']=='aluminium-head-jamb-return')
        self.assertLess(joined['expectedVolumeMm3'],512075.05824298417)
        self.assertGreater(joined['maximumJoinedVolumeMm3'],512075.05824298417)
        self.assertAlmostEqual(next(p['expectedVolumeMm3'] for p in native if p['id']=='aluminium-sill'),119783.11438723429)
        self.assertAlmostEqual(next(p['expectedVolumeMm3'] for p in native if p['id']=='seal-perimeter'),28512.8)

if __name__ == '__main__': unittest.main()
