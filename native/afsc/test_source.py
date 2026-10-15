"""Source-contract checks; native geometry acceptance remains in proof.json."""
import ast,json,math,unittest
from pathlib import Path

class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads(Path(__file__).with_name('source.json').read_text(encoding='utf-8'))
    def test_nominal_module_is_not_frame_dimension(self):
        s=self.source
        self.assertEqual(s['frameSizeMm'],[m*100-s['moduleAllowanceMm'] for m in s['module']])
        self.assertEqual(s['frameSizeMm'],[880,1180])
    def test_glazing_has_empty_18mm_cavities(self):
        panes=self.source['glazingDepthRangesMm']
        self.assertEqual([b-a for a,b in panes],[4,4,4])
        self.assertEqual([panes[i+1][0]-panes[i][1] for i in range(2)],[18,18])
        self.assertEqual(panes[-1][1]-panes[0][0],48)
    def test_native_sketch_edges_and_recorded_deviation(self):
        for name,profile in self.source['profiles'].items():
            pts=profile['pointsMm']
            self.assertGreaterEqual(len(pts),3,name)
            self.assertTrue(all(math.isfinite(v) for p in pts for v in p),name)
            lengths=[math.dist(a,b) for a,b in zip(pts,pts[1:]+pts[:1])]
            self.assertGreater(min(lengths),.89,name)
            self.assertLessEqual(profile['maximumOutlineDeviationMm'],1,name)
            # Revit warns for almost-45-degree chamfers as well as almost-axis
            # lines. Millimetre rounding must preserve these tiny chamfers.
            for a,b in zip(pts,pts[1:]+pts[:1]):
                dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1])
                if min(dx,dy)>.5 and abs(dx-dy)<.01:self.assertAlmostEqual(dx,dy,places=7,msg=name)
    def test_distinct_source_sections_and_fixed_scope(self):
        s=self.source
        for prefix in ['frame','sash','sashAluminium']:
            self.assertNotEqual(s['profiles'][prefix+'Head']['pointsMm'],s['profiles'][prefix+'Sill']['pointsMm'])
        self.assertFalse(s['nativeParameterFlex']);self.assertFalse(s['manufacturerApproved'])
        self.assertEqual(s['openingAngleDegrees'],0)

    def test_corner_cut_volume_math_handles_outer_returns(self):
        tree=ast.parse(Path(__file__).with_name('build_closed.py').read_text(encoding='utf-8'))
        tree.body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ['area_moment','positive_moment']]
        namespace={};exec(compile(tree,'volume-math','exec'),namespace)
        # A 2 mm radial strip, 1 mm thick, loses two 45-degree end triangles.
        shape=[[0,0],[2,0],[2,1],[0,1]]
        area,moment=namespace['area_moment'](shape)
        self.assertEqual(area*100-2*moment,196)
        # An outside return (negative radial coordinate) is not extended by a cut.
        self.assertEqual(namespace['positive_moment']([[-2,0],[2,0],[2,1],[-2,1]]),2)
        self.assertEqual(namespace['area_moment'](list(reversed(shape))),(area,moment))

if __name__=='__main__':unittest.main()
