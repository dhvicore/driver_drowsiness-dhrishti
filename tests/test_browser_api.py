"""Browser frame input checks; no physical webcam or model inference required."""
import unittest
from unittest.mock import patch

import cv2
import numpy as np

import server


class BrowserInputTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        self.capture = server.BrowserCapture()
        self.running = patch.object(server.monitor, 'running', True)
        self.capture_patch = patch.object(server.monitor, '_capture', self.capture, create=True)
        self.running.start()
        self.capture_patch.start()

    def tearDown(self):
        self.capture_patch.stop()
        self.running.stop()

    def test_frames_require_an_active_browser_session(self):
        with patch.object(server.monitor, 'running', False):
            self.assertEqual(self.client.post('/api/frame', data=b'x').status_code, 409)
        with patch.object(server.monitor, '_capture', object()):
            self.assertEqual(self.client.post('/api/frame', data=b'x').status_code, 409)

    def test_reject_invalid_and_oversized_uploads(self):
        self.assertEqual(self.client.post('/api/frame', data=b'not an image').status_code, 400)
        self.assertEqual(self.client.post('/api/frame', data=b'x' * 2_000_001).status_code, 413)

    def test_decode_browser_jpeg_and_keep_only_latest_frame(self):
        for value in (0, 255):
            ok, jpeg = cv2.imencode('.jpg', np.full((36, 64, 3), value, np.uint8))
            self.assertTrue(ok)
            response = self.client.post('/api/frame', data=jpeg.tobytes(), content_type='image/jpeg')
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.capture.frames.qsize(), 1)
        ok, frame = self.capture.read()
        self.assertTrue(ok)
        self.assertGreater(frame.mean(), 250)

    def test_start_route_selects_browser_input(self):
        with patch.object(server.monitor, 'start', return_value=(True, None)) as start:
            self.assertEqual(self.client.post('/api/start', json={'source': 'browser'}).status_code, 200)
            start.assert_called_once_with(browser=True)


if __name__ == '__main__':
    unittest.main()
