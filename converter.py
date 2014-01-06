#!/usr/bin/env python3
#coding: utf-8

'''Usage: python converter.py SOURCE_SCRIPT OUTPUT_DESTINATION
Convert your grease monkey script into chrome content script extension.
'''

import os
import shutil
import re
import json
from urllib import request
from collections import defaultdict


def parse_metadata(raw):
    '''Parse script meta data into dict.

    e.g.,:

        // ==UserScript==
        // @name           hello world
        // @namespace      http://foobar.example.com
        // @version        3.1.4
        // @description    This is a test description.
        // @match          http://a.example.com
        // @grant          GM_getValue
        // @grant          GM_setValue
        // ==/UserScript==

    should be parsed into:

        {
            'name': u'hello world',
            'namespace': u'http://foobar.example.com',
            'version': u'3.1.4',
            'description': u'This is a test description.',
            'match': u'http://a.example.com',
            'grant': [u'GM_getValue', u'GM_setValue']
        }

    :param raw: unparsed metadata
    '''
    BEGIN = re.compile('==UserScript==', re.IGNORECASE)
    END = re.compile('==/UserScript==', re.IGNORECASE)
    KV = re.compile('//\s*@(\w+)\s*(.+)')
    LIST_KEYS = ['require', 'grant']

    lines = END.split(BEGIN.split(raw)[-1])[0].split('\n')
    _parsed, parsed = defaultdict(list), {}

    for line in lines:
        line = line.strip()
        if not line.startswith('//'):
            continue
        check = KV.match(line)
        if check:
            k, v = check.group(1).strip().lower(), check.group(2).strip()
            _parsed[k].append(v)

    for k, v in _parsed.items():
        if len(v) > 1 or k in LIST_KEYS:
            parsed[k] = [i for i in v]
        else:
            # flatten the value if there is no duplicated key
            parsed[k] = v[0]

    return parsed


def get_remote_script(script_dest):
    '''Retrieve remote script's name and content

    :param script_dest: remote script's url
    '''
    check = re.compile('http[s]{0,1}://.*/(.*\.js)').match(script_dest)
    if not check:
        return
    name = check.group(1)
    with request.urlopen(script_dest) as remote:
        return (name, remote.read().decode('utf-8'))


def get_grant_script(api, name_tmpl=None, scripts_path=None):
    '''Retrieve local grant api script's name and content.

    If requested grant api script not found, raise `Exception`

    :param api: grant api's name
    :param name_tmpl: grant api scripts name template,
                      default is `'grant%s.js'`
    :param scripts_path: grant api scripts path,
                         default is current directory
    '''
    name_tmpl = name_tmpl or 'grant%s.js'
    scripts_path = scripts_path or os.path.dirname(os.path.abspath(__file__))

    name = name_tmpl % api
    path = os.path.join(scripts_path, name)
    if not os.path.exists(path):
        raise Exception('Grant api script %s not found! (%s)' % (api, path))
    with open(path, 'r') as grant_script:
        return (name, grant_script.read())


def build_manifest(metadata, script_name):
    '''Build chrome extension's manifest and scripts from metadata.

    :param metadata: parsed metadata from `parse_metadata`
    :param script_name: script's name
    '''
    remote_scripts = dict(map(get_remote_script, metadata.get('require', [])))
    grant_scripts = dict(map(get_grant_script, metadata.get('grant', [])))
    scripts = list(remote_scripts.keys()) + list(grant_scripts.keys())
    
    manifest = {
        'manifest_version': 2,
        'name': metadata['name'],
        'description': metadata['description'],
        'version': metadata['version'],
        'content_scripts': [{
            'matches': metadata['match'],
            'js': scripts + [script_name],
            'run_at': 'document_end',
            'all_frames': True
        }],
        'permissions': metadata['match']
    }

    return manifest, remote_scripts, grant_scripts


def create_ext_path(dest_path, manifest, scripts):
    '''Create converted extension path tree.

    :param dest_path: output path
    :param manifest: converted manifest dict
    :param scripts: scripts list, item as (name, content) tuple
    '''

    def write(name, content):
        with open(os.path.join(dest_path, name), 'w') as f:
            f.write(content)

    try:
        shutil.rmtree(dest_path)
    except:
        pass
    os.mkdir(dest_path)

    write('manifest.json', json.dumps(manifest, indent=4))
    for name, content in scripts:
        write(name, content)


def convert(source_path, dest_path):
    '''Convert a grease monkey script into Chrome extension
    content script.
    
    :param source_path: source script path
    :param dest_path: output path
    '''
    source_path = os.path.abspath(source_path)
    with open(source_path, 'r') as source:
        script = (os.path.basename(source_path), source.read())

    name, content = script
    metadata = parse_metadata(content)
    manifest, remote, grant = build_manifest(metadata, name)
    scripts = list(remote.items()) + list(grant.items()) + [script]

    create_ext_path(dest_path, manifest, scripts)


def _cli():
    import sys
    if len(sys.argv) > 2:
        source, dest = sys.argv[-2:]
        convert(source, dest)
        print('Convert finished!', end='')
    else:
        print(__doc__, end='')


if __name__ == '__main__':
    _cli()
