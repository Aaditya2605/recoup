import json
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import app


class AppWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db, self.old_uploads = app.DB, app.UPLOADS
        app.DB = Path(self.temp.name) / "recoup.db"
        app.UPLOADS = Path(self.temp.name) / "uploads"
        app.init_db()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        app.DB, app.UPLOADS = self.old_db, self.old_uploads
        self.temp.cleanup()

    def request(self, path, method="GET", payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def test_sample_archive_restore_and_delete(self):
        sample = self.request("/api/demo")
        self.assertEqual([], self.request("/api/state")["cases"])

        created = self.request("/api/cases", "POST", {**sample, "synthetic": True})
        case_id = created["id"]
        self.assertTrue(self.request(f"/api/cases/{case_id}")["synthetic"])

        self.request(f"/api/cases/{case_id}/archive", "POST", {})
        self.assertTrue(self.request("/api/state")["cases"][0]["archived"])
        self.request(f"/api/cases/{case_id}/restore", "POST", {})
        self.assertFalse(self.request("/api/state")["cases"][0]["archived"])

        self.request(f"/api/cases/{case_id}", "DELETE")
        self.assertEqual([], self.request("/api/state")["cases"])
        self.assertEqual(3, len(list((app.UPLOADS / ".deleted" / case_id).iterdir())))


if __name__ == "__main__":
    unittest.main()
