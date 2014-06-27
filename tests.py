# coding: utf-8

import unittest

from converter import (parse_metadata, get_remote_script, get_grant_script,
                       build_manifest)


class TestParsing(unittest.TestCase):

    def testParseMetadata(self):
        block_tmpl = '// ==UserScript==\n %s\n// ==/UserScript=='
        parsed = parse_metadata(block_tmpl % ('// @name hello world'))
        self.assertEqual(parsed['name'], 'hello world')

        parsed = parse_metadata(block_tmpl % ('@name hello world'))
        self.assertNotIn('name', parsed)

        raw = '''
        // ==UserScript==
        // @name           hello world
        // @namespace      http://foobar.example.com
        // @version        3.1.4
        // @description    This is a test description.
        // @match          http://a.example.com
        // @foo     1
        // @foo     2
        // ==/UserScript==
        '''
        parsed = parse_metadata(raw)
        self.assertIsInstance(parsed['foo'], list)

    def testGetRemoteScript(self):
        remote = 'http://code.jquery.com/jquery-2.0.3.min.js'
        name, content = get_remote_script(remote)
        self.assertEqual(name, 'jquery-2.0.3.min.js')

        self.assertIsNone(get_remote_script('123.js'))

    def testGetGrantScript(self):
        self.assertRaises(Exception, get_grant_script, '123')

        name, content = get_grant_script('GM_xmlhttpRequest')
        self.assertEqual(name, 'grantGM_xmlhttpRequest.js')

    def testBuildManifest(self):
        raw = '''
        // ==UserScript==
        // @name           hello world
        // @namespace      http://foobar.example.com
        // @version        3.1.4
        // @description    This is a test description.
        // @match          http://a.example.com
        // @grant          GM_xmlhttpRequest
        // @require        http://code.jquery.com/jquery-2.0.3.min.js
        // ==/UserScript==
        '''
        metadata = parse_metadata(raw)
        manifest, remote, grant = build_manifest(metadata, '1.js')

        self.assertEqual(manifest['name'], 'hello world')
        self.assertEqual(manifest['manifest_version'], 2)
        self.assertEqual(len(manifest['content_scripts']), 1)
        self.assertIn('jquery-2.0.3.min.js', remote)
        self.assertIn('grantGM_xmlhttpRequest.js', grant)

    def testRemoteSciprtsOrder(self):
        raw = '''
        // ==UserScript==
        // @name           hello world
        // @namespace      http://foobar.example.com
        // @version        3.1.4
        // @description    This is a test description.
        // @match          http://a.example.com
        // @require http://code.jquery.com/jquery-2.0.3.min.js
        // @require http://code.jquery.com/jquery-2.1.1.min.js
        // @require http://code.jquery.com/jquery-2.0.0.min.js
        // ==/UserScript==
        '''
        metadata = parse_metadata(raw)
        manifest, remote, grant = build_manifest(metadata, '1.js')
        scripts = manifest['content_scripts'][0]['js']
        self.assertIsInstance(scripts, list)
        self.assertEqual(scripts[0], 'jquery-2.0.3.min.js')
        self.assertEqual(scripts[1], 'jquery-2.1.1.min.js')
        self.assertEqual(scripts[2], 'jquery-2.0.0.min.js')

    def testMergeKey(self):
        raw = '''
        // ==UserScript==
        // @name           hello world
        // @namespace      http://foobar.example.com
        // @version        3.1.4
        // @description    This is a test description.
        // @match          http://a.example.com
        // @grant          GM_xmlhttpRequest
        // @permissions    activeTab
        // @manifest_version 3
        // ==/UserScript==
        '''
        metadata = parse_metadata(raw)
        manifest, remote, grant = build_manifest(metadata, '1.js')

        # Merge list.
        self.assertIn('activeTab', manifest['permissions'])

        # Metadata block should have higher priority.
        self.assertEqual(3, int(manifest['manifest_version']))

    def testPredefinedManifest(self):
        raw = '''
        // ==UserScript==
        // @name           hello world
        // @namespace      http://foobar.example.com
        // @version        3.1.4
        // @description    This is a test description.
        // @match          http://a.example.com
        // @grant          GM_xmlhttpRequest
        // @permissions    activeTab
        // @manifest_version 3
        // ==/UserScript==
        '''

        predefined = {
            'manifest_version': 1,
            'background': {}
        }

        metadata = parse_metadata(raw)
        manifest, remote, grant = build_manifest(metadata, '1.js', predefined)

        # Merge list.
        self.assertIn('activeTab', manifest['permissions'])

        # Predefined manifest should have higher priority.
        self.assertEqual(1, int(manifest['manifest_version']))

        # Has extra keys:
        self.assertIn('background', manifest)


if __name__ == '__main__':
    unittest.main()
