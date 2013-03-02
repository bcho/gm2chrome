#coding: utf-8

import re
import sys
import os
import shutil
import urllib
import json

EXTENSION_PATH = os.path.abspath('ext/')
GRANT_SCRIPT_PATH = os.path.abspath('gm2chrome')


def get_remote_scripts(scripts):
    ret, is_remote_script = [], re.compile(r'http[s]{0,1}://.*/(.*\.js)')
    for script in scripts:
        m = is_remote_script.match(script)
        if m:
            f = urllib.urlopen(script)
            with open(m.groups()[0], 'w') as s:
                s.write(f.read())
            f.close()
            ret.append(m.groups()[0])
        else:
            ret.append(script)
    return ret


def get_grant_scripts(scripts):
    return ['grant%s.js' % script for script in scripts]


def parse_manifest(lines):
    manifest, r = {}, re.compile(r'//\s*@(\w+)\s*(.*)')
    for line in lines:
        g = r.match(line)
        if g:
            if not manifest.get(g.groups()[0], None):
                manifest[g.groups()[0]] = [g.groups()[1].strip()]
            else:
                manifest[g.groups()[0]].append(g.groups()[1].strip())
    return manifest


def build_ext_manifest(manifest, script):
    return {
        'manifest_version': 2,
        'name': manifest['name'][0],
        'description': manifest['description'][0],
        'version': manifest['version'][0],

        'content_scripts': [{
            'matches': manifest['match'],
            'js': get_remote_scripts(manifest.get('require', [])) +
                  get_grant_scripts(manifest.get('grant', [])) +
                  [script],
            'run_at': 'document_end',
            'all_frames': True
        }],

        'permissions': manifest['match']
    }


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            gm_manifest = parse_manifest(f.readlines())
            manifest = build_ext_manifest(gm_manifest, sys.argv[1])
            with open('manifest.json', 'w') as chrome_manifest:
                chrome_manifest.write(json.dumps(manifest))
            
            try:
                shutil.rmtree(EXTENSION_PATH)
            except:
                pass
            os.mkdir(EXTENSION_PATH)
            shutil.move('manifest.json', EXTENSION_PATH)
            for scope in manifest['content_scripts']:
                for script in scope['js']:
                    if script == sys.argv[1]:
                        shutil.copy(script, EXTENSION_PATH)
                    elif script.startswith('grant'):
                        shutil.copy(os.path.join(GRANT_SCRIPT_PATH, script),
                                EXTENSION_PATH)
                    else:
                        shutil.move(script, EXTENSION_PATH)
    else:
        print 'python %s your_script.js' % sys.argv[0]
    


if __name__ == '__main__':
    main()
