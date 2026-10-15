import json,unittest
from pathlib import Path
from corner_math import boundary,inverse,corner_spec,integral,frame_sill_spec,cut_region,KNEE,OFFSETS

class CornerTests(unittest.TestCase):
    def test_all_shared_return_vertices_land_on_same_cut(self):
        s=json.loads(Path(__file__).with_name('source.json').read_text())
        profiles=s['nativeProfiles']
        for jamb in ['Left','Right']:
            for horizontal in ['Head','Sill']:
                spec=corner_spec(profiles,jamb,horizontal)
                for u,d in s['profiles']['sashAluminiumLeft']['pointsMm'][5:36]:
                    self.assertAlmostEqual(boundary(spec,u+OFFSETS[jamb]),u+OFFSETS[horizontal],places=8)
                self.assertAlmostEqual(boundary(spec,spec['kneeU']),spec['kneeV'])
                for u in [0,33,60,80,100,140]:self.assertAlmostEqual(inverse(spec,boundary(spec,u)),u)

    def test_piecewise_cut_volume_integral_crosses_knee(self):
        rectangle=[[0,0],[20,0],[20,2],[0,2]]
        spec={'kneeU':10,'kneeV':20,'slope':2,'intercept':0,'delta':10}
        # 2 * (integral(2u,0..10) + integral(u+10,10..20)).
        self.assertAlmostEqual(integral(rectangle,spec),700)
        self.assertAlmostEqual(integral(list(reversed(rectangle)),spec),700)

    def test_refinement_is_bounded_and_standard_trim_is_explicit(self):
        s=json.loads(Path(__file__).with_name('source.json').read_text())
        self.assertFalse(s['includePlasterTrim'])
        self.assertTrue(s['completePlan'])
        self.assertEqual(len(s['nativeProfileRefinements']),4)
        self.assertTrue(all(r['maximumDeviationFromSimplifiedSourceMm']<=1 for r in s['nativeProfileRefinements']))

    def test_different_frame_face_widths_share_the_same_cut(self):
        spec=frame_sill_spec()
        self.assertAlmostEqual(boundary(spec,3.081),9.72)
        self.assertAlmostEqual(boundary(spec,40.2),28.279)
        for is_jamb in [False,True]:
            polygon=cut_region(spec,is_jamb)
            self.assertTrue(all(-150<=u<=250 for u,v in polygon))

if __name__=='__main__':unittest.main()
