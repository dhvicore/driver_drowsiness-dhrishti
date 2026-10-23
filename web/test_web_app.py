"""Browser adapter regressions; no physical camera or network is used."""
import ast
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import app
from features import calculate_ear, calculate_mar, LEFT_EYE, RIGHT_EYE

class BrowserTests(unittest.TestCase):
    def test_feature_formulas_match_desktop(self):
        nodes=[]
        for node in ast.parse((app.ROOT/'main.py').read_text()).body:
            if isinstance(node,ast.FunctionDef) and node.name in {'get_point','distance','calculate_ear','calculate_mar'}:
                nodes.append(node)
        import math
        scope=dict(math=math,MOUTH_LEFT=61,MOUTH_RIGHT=291,MOUTH_UPPER=13,MOUTH_LOWER=14)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<desktop formulas>','exec'),scope)
        rng=np.random.default_rng(12)
        landmarks=[SimpleNamespace(x=float(x),y=float(y)) for x,y in rng.random((478,2))]
        for eye in [LEFT_EYE,RIGHT_EYE]:
            self.assertEqual(calculate_ear(landmarks,eye,640,480),scope['calculate_ear'](landmarks,eye,640,480))
        self.assertEqual(calculate_mar(landmarks,640,480),scope['calculate_mar'](landmarks,640,480))

    def test_session_isolation(self):
        a,b=app.Session(),app.Session()
        a.engine.update(.15,.6)
        a.add_event('Only visitor A')
        self.assertFalse(b.engine.ear_history)
        self.assertFalse(b.events)
        self.assertIsNot(a.head,b.head)

    def test_missing_frame_does_not_start_monitoring(self):
        s=app.Session()
        result=app.monitor(None,False,s)
        self.assertIn('Ready',result[1])
        self.assertFalse(s.engine.ear_history)

    def test_no_face_resets_previous_closure(self):
        s=app.Session()
        s.engine.update(.15,.6)
        with patch.object(app,'face_model') as factory:
            factory.return_value.detect.return_value=SimpleNamespace(face_landmarks=[])
            result=app.monitor(np.zeros((200,300,3),dtype=np.uint8),False,s)
        self.assertIn('No face',result[1])
        self.assertFalse(s.engine.ear_history)
        self.assertEqual(s.last_label,'NO FACE')

    def test_gap_resets_instead_of_extending_closure(self):
        s=app.Session()
        s.engine.update(.15,.6)
        old=s.engine
        s.last_frame=10
        with patch.object(app.time,'monotonic',return_value=13),patch.object(app,'face_model') as factory:
            factory.return_value.detect.return_value=SimpleNamespace(face_landmarks=[])
            app.monitor(np.zeros((200,300,3),dtype=np.uint8),False,s)
        self.assertIsNot(s.engine,old)
        self.assertTrue(any('gap' in e[1] for e in s.events))

if __name__=='__main__':unittest.main()
