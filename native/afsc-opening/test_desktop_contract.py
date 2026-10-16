import unittest,json,hashlib,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sidehung_contract',Path(__file__).with_name('desktop_contract.py'));contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
class ContractTests(unittest.TestCase):
 def setUp(self):
  self.definition=json.loads((ROOT/'public/native/sidehung/definition.json').read_text(encoding='utf-8'))
  self.request={'kind':'lithic-build-request','schemaVersion':'0.1','definition':self.definition,'approvedAt':'2026-10-16T10:00:00.000Z','configuration':{'width':880,'height':1180,'interior':'timber','exterior':'graphite','openingAngleDegrees':45},'geometryEngine':'side-hung-native-snapshot/0.1','units':'mm','parts':[],'nativeStatus':'not-built'}
 def validate(self):
  raw=json.dumps(self.request).encode('utf-8');return contract.validate(raw,{'builder':contract.BUILDER,'requestSha256':hashlib.sha256(raw).hexdigest(),'nativeParameterFlex':False,'geometryMode':'fixed-size-snapshot'},self.definition)
 def test_accepts_reviewed_angles_and_finishes(self):
  for angle in [0,15,45,90]:
   self.request['configuration']['openingAngleDegrees']=angle;self.assertEqual(self.validate()[0]['configuration']['openingAngleDegrees'],angle)
 def test_rejects_other_sizes(self):
  self.request['configuration']['width']=900
  with self.assertRaises(ValueError):self.validate()
 def test_rejects_bad_angles(self):
  for angle in [-1,91,float('nan'),float('inf'),True,'45',None]:
   self.request['configuration']['openingAngleDegrees']=angle
   with self.assertRaises(ValueError):self.validate()
 def test_rejects_changed_definition(self):
  self.request['definition']=dict(self.definition,revision=999)
  with self.assertRaises(ValueError):self.validate()
 def test_rejects_unrecognised_fields(self):
  self.request['configuration']['handing']='right'
  with self.assertRaises(ValueError):self.validate()
if __name__=='__main__':unittest.main()
