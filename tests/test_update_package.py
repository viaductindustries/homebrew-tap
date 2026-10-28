import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_package import ROOT, registry, render, release_asset, version_tuple, sha256_download, main


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.package = registry()['cert-lab']
        self.template = (ROOT / self.package['template']).read_text()
        self.current = render(None, self.template, '1.2.3', 'a' * 64)

    def test_initial_cask_uses_downloaded_hash(self):
        self.assertIn('version "1.2.3"', self.current)
        self.assertIn('sha256 "' + 'a' * 64 + '"', self.current)
        self.assertNotIn('@VERSION@', self.current)

    def test_update_only_changes_version_and_hash(self):
        actual = render(self.current, self.template, '1.3.0', 'b' * 64)
        self.assertEqual(actual, self.current.replace('1.2.3', '1.3.0').replace('a' * 64, 'b' * 64))

    def test_repeat_is_identical(self):
        self.assertEqual(self.current, render(self.current, self.template, '1.2.3', 'a' * 64))

    def test_numeric_version_ordering(self):
        self.assertGreater(version_tuple('1.10.0'), version_tuple('1.9.0'))

    def test_downgrade_rejected(self):
        with self.assertRaisesRegex(ValueError, 'downgrade'):
            render(self.current, self.template, '1.2.2', 'b' * 64)

    def test_replaced_release_rejected(self):
        with self.assertRaisesRegex(ValueError, 'existing version'):
            render(self.current, self.template, '1.2.3', 'b' * 64)

    def test_unsupported_versions(self):
        for value in ['1.0.0-beta.1', '01.2.3', '1.2', '../main', '1.2.3\n', '1.0.0;echo bad']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                version_tuple(value)

    def test_checksum_must_be_hex(self):
        with self.assertRaises(ValueError):
            render(self.current, self.template, '1.3.0', 'not a checksum')

    def test_multiple_architecture_hashes_need_custom_support(self):
        with self.assertRaises(ValueError):
            render(self.current + '\n  sha256 "' + 'b' * 64 + '"\n', self.template, '1.3.0', 'c' * 64)

    def test_edited_definition_rejected(self):
        with self.assertRaisesRegex(ValueError, 'template'):
            render(self.current.replace('Cert Lab', 'Other'), self.template, '1.3.0', 'b' * 64)

    def test_formula_version_comes_from_url(self):
        template = (ROOT / registry()['ghsecretsync']['template']).read_text()
        current = render(None, template, '1.2.3', 'a' * 64)
        self.assertIn('/download/v1.2.3/ghsecretsync_1.2.3_source.tar.gz"', current)
        self.assertNotIn('  version "', current)
        actual = render(current, template, '1.3.0', 'b' * 64)
        self.assertEqual(actual, current.replace('1.2.3', '1.3.0').replace('a' * 64, 'b' * 64))
        with self.assertRaisesRegex(ValueError, 'downgrade'):
            render(current, template, '1.2.2', 'b' * 64)

    def test_formula_url_versions_must_agree(self):
        template = (ROOT / registry()['ghsecretsync']['template']).read_text()
        current = render(None, template, '1.2.3', 'a' * 64).replace('_1.2.3_', '_1.2.4_')
        with self.assertRaisesRegex(ValueError, 'template'):
            render(current, template, '1.3.0', 'b' * 64)

    def release(self):
        return {'tag_name': 'v1.0.0', 'draft': False, 'prerelease': False, 'assets': [{
            'name': 'Cert-Lab-1.0.0-universal.zip', 'size': 123, 'state': 'uploaded',
            'browser_download_url': 'https://github.com/viaductindustries/cert-lab/releases/download/v1.0.0/Cert-Lab-1.0.0-universal.zip'}]}

    def test_asset_found(self):
        self.assertEqual(release_asset(self.release(), self.package, 'v1.0.0')['size'], 123)

    def test_missing_asset_blocks_publication(self):
        release = self.release(); release['assets'] = []
        with self.assertRaisesRegex(ValueError, 'missing'):
            release_asset(release, self.package, 'v1.0.0')

    def test_draft_and_prerelease_rejected(self):
        for flag in ['draft', 'prerelease']:
            release = self.release(); release[flag] = True
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                release_asset(release, self.package, 'v1.0.0')

    def test_wrong_download_host_rejected(self):
        release = self.release(); release['assets'][0]['browser_download_url'] = 'https://example.com/evil.zip'
        with self.assertRaises(ValueError):
            release_asset(release, self.package, 'v1.0.0')

    def test_incomplete_asset_rejected(self):
        release = self.release(); release['assets'][0]['state'] = 'new'
        with self.assertRaises(ValueError):
            release_asset(release, self.package, 'v1.0.0')

    def test_wrong_owner_rejected_before_network_access(self):
        args = ['update_package.py', '--package', 'cert-lab', '--tag', 'v1.0.0',
                '--source-repository', 'viaductindustries/another-project']
        with patch.object(sys, 'argv', args), patch('urllib.request.urlopen') as request:
            with self.assertRaisesRegex(ValueError, 'does not own'):
                main()
            request.assert_not_called()

    def test_download_hash_verified(self):
        import hashlib
        asset = self.release()['assets'][0]
        asset['size'] = 3
        asset['digest'] = 'sha256:' + hashlib.sha256(b'zip').hexdigest()
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'zip')):
            self.assertEqual(sha256_download(asset), asset['digest'][7:])

    def test_truncated_download_rejected(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'zip')):
            with self.assertRaisesRegex(ValueError, 'size'):
                sha256_download(self.release()['assets'][0])

    def test_download_digest_mismatch_rejected(self):
        asset = self.release()['assets'][0]
        asset.update(size=3, digest='sha256:' + 'a' * 64)
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'zip')):
            with self.assertRaisesRegex(ValueError, 'checksum'):
                sha256_download(asset)

    def test_registry_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = dict(self.package, path='../outside.rb')
            (root / 'packages.json').write_text(json.dumps({'cert-lab': package}))
            with self.assertRaisesRegex(ValueError, 'path'):
                registry(root)


if __name__ == '__main__':
    unittest.main()
