import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from app.core.exceptions import NotFoundError, ValidationError
from app.services.payload_store_service import PayloadStoreService


class PayloadLoadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.service = PayloadStoreService()
        self.service.settings = self.service.settings.model_copy(update={
            "query_log_file_dir": self.tmp.name,
            "query_log_inline_max_bytes": 1,
        })
        self.record = SimpleNamespace(
            trace_id="test-query", payload_store_path=None,
            request_plain_text=None, request_cipher_text=None,
            response_plain_text=None, response_raw_text=None,
            created_at=datetime.now(), started_at=None,
        )

    def store(self, kind, text):
        return self.service.store_text(
            trace_id=self.record.trace_id, kind=kind, text=text, ext="json"
        )

    def test_database_content_takes_precedence(self):
        raw = self.store("response_raw", '{"encrypted":"value"}')
        self.record.payload_store_path = raw.store_path
        self.record.response_plain_text = '{"list":[{"id":1}]}'
        self.assertEqual(self.service.load_record_json(self.record), {"list": [{"id": 1}]})
        self.assertEqual(self.service.load_record_text(self.record, "response_plain").source, "DB")

    def test_each_kind_loads_its_own_file(self):
        texts = {
            "response_raw": '{"encrypted":"value"}',
            "response_plain": '{"list":[{"id":1}]}',
            "request_plain": '{"page":1}',
            "request_cipher": 'encrypted-request',
        }
        for kind, text in texts.items():
            stored = self.store(kind, text)
            if kind == "response_raw":
                self.record.payload_store_path = stored.store_path
        for kind, text in texts.items():
            with self.subTest(kind=kind):
                loaded = self.service.load_record_text(self.record, kind)
                self.assertEqual(loaded.text, text)
                self.assertEqual(loaded.source, "FILE")

    def test_wrong_kind_is_never_used_as_fallback(self):
        raw = self.store("response_raw", '{"encrypted":"value"}')
        self.record.payload_store_path = raw.store_path
        with self.assertRaises(NotFoundError):
            self.service.load_record_json(self.record)

    def test_date_directory_without_representative_path(self):
        self.store("response_plain", '{"list":[]}')
        self.assertEqual(self.service.load_record_json(self.record), {"list": []})

    def test_flat_legacy_directory(self):
        path = Path(self.tmp.name) / "test-query_response_plain.txt"
        path.write_text('{"list":[]}', encoding="utf-8")
        self.assertEqual(self.service.load_record_json(self.record), {"list": []})

    def test_invalid_json_is_an_error_for_database_and_file(self):
        self.record.response_plain_text = '{broken'
        with self.assertRaises(ValidationError):
            self.service.load_record_json(self.record)
        self.record.response_plain_text = None
        self.store("response_plain", '{broken')
        with self.assertRaises(ValidationError):
            self.service.load_record_json(self.record)

    def test_missing_payload_and_invalid_kind_are_explicit_errors(self):
        with self.assertRaises(NotFoundError):
            self.service.load_record_json(self.record)
        with self.assertRaises(ValidationError):
            self.service.load_record_text(self.record, "../response_plain")


if __name__ == "__main__":
    unittest.main()
