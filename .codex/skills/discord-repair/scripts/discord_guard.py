#!/usr/bin/env python3
"""Quiet local Discord Stable patch recovery; never opens GUI or restarts Discord."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import tarfile
import tempfile
import time
from dataclasses import dataclass

BASE = Path('/Users/mh/Library/Application Support')
CLI = BASE / 'discord-repair/bin/VencordInstallerCli-darwin'
CLI_SHA = '7efb9325d8f150b723251262416cf3a4c1a552a98c7a65378b950a6135b64005'

@dataclass
class Config:
    app: Path = Path('/Applications/Discord.app')
    base: Path = BASE / 'Vencord'
    dist: Path = Path('/Users/mh/code/hoerbert/Vencord/dist')
    state: Path = BASE / 'discord-repair'
    cli: Path = CLI
    cli_sha: str = CLI_SHA
    now: object = time.time
    process: object = None
    runner: object = subprocess.run
    stability: float = 60

    @property
    def resources(self): return self.app / 'Contents/Resources'
    @property
    def settings(self): return self.base / 'settings/settings.json'


def digest(path):
    try: return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError: return 'missing'


def read_json(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError): return {}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='receipt-')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def running(c):
    if c.process: return c.process()
    r = subprocess.run(['/bin/ps', '-axo', 'comm='], capture_output=True, text=True, timeout=5)
    # Unknown process state defers repair. Include updater/helpers during restart.
    return r.returncode != 0 or any(str(c.app) + '/' in line or 'shipit' in line.lower() or ('discord' in line.lower() and ('updat' in line.lower() or 'helper' in line.lower())) for line in r.stdout.splitlines())


def valid_asar(path):
    """Check packed archive bounds and its Discord package entry before patching."""
    try:
        b = path.read_bytes()
        if len(b) < 16: return False
        size, header_size, payload_size, json_size = struct.unpack('<4I', b[:16])
        if size != 4 or header_size != payload_size + 4 or json_size > payload_size - 4 or header_size + 8 > len(b): return False
        files = json.loads(b[16:16+json_size])['files']
        data_start = 8 + header_size
        def walk(entries):
            for name, entry in entries.items():
                if 'files' in entry:
                    if not walk(entry['files']): return False
                elif entry.get('unpacked') or 'link' in entry:
                    return False
                else:
                    off, length = int(entry['offset']), entry['size']
                    if off < 0 or not isinstance(length, int) or length < 0 or data_start + off + length > len(b): return False
            return True
        if not walk(files): return False
        package = files['package.json']
        start = data_start + int(package['offset'])
        meta = json.loads(b[start:start+package['size']])
        return meta.get('name') == 'discord' and isinstance(meta.get('main'), str) and meta['main'].removeprefix('./') in files
    except (OSError, ValueError, KeyError, TypeError, struct.error):
        return False


def inspect(c):
    renderer = c.dist / 'renderer.js'
    try: blob = renderer.read_bytes()
    except OSError: blob = b''
    plugins = read_json(c.settings).get('plugins', {})
    if not isinstance(plugins, dict): plugins = {}
    app = c.resources / 'app.asar'; original = c.resources / '_app.asar'
    try: shim = app.read_bytes()
    except OSError: shim = b''
    expected = ('require(' + json.dumps(str(c.base / 'dist/patcher.js')) + ')').encode()
    checks = {
        'custom_dist_link': (c.base / 'dist').resolve() == c.dist.resolve(),
        'patcher_present': (c.dist / 'patcher.js').is_file() and (c.dist / 'patcher.js').stat().st_size > 0,
        'renderer_plugins_present': all(x in blob for x in [b'AutoStream', b'AquaMuteSync']),
        'plugins_enabled': all(isinstance(plugins.get(x), dict) and plugins[x].get('enabled') is True for x in ['AutoStream','AquaMuteSync']),
        'shim_present': expected in shim and len(shim) < 65536,
        'original_present': valid_asar(original),
    }
    paths = [c.dist/'patcher.js', renderer, c.settings, app, original]
    fingerprint = hashlib.sha256('|'.join(digest(p) for p in paths).encode()).hexdigest()
    healthy = all(checks.values())
    active = running(c)
    return {'checked_at': c.now(), 'configuration_healthy': healthy,
            'state': 'configuration_healthy' if healthy else ('running_defer' if active else 'needs_attention'),
            'discord_running': active, 'checks': checks, 'fingerprint': fingerprint,
            'repair': {'attempted': False, 'result': 'no_op' if healthy else 'check_only'}}


def allowed(c, s):
    return all(s['checks'][k] for k in ['custom_dist_link','patcher_present','renderer_plugins_present','plugins_enabled']) and not s['checks']['shim_present'] and not (c.resources/'_app.asar').exists() and valid_asar(c.resources/'app.asar')


def stable(c):
    for p in [c.resources/'app.asar', c.dist/'patcher.js', c.dist/'renderer.js']:
        try:
            st = p.stat()
            if c.now() - max(st.st_mtime, st.st_ctime) < c.stability: return False
        except OSError: return False
    return True


def run(c, repair=False):
    c.state.mkdir(parents=True, exist_ok=True)
    with (c.state/'.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return {'state':'another_check_running'}
        s = inspect(c)
        def finish(result):
            s['repair'] = {'attempted':False,'result':result}
            save(c.state/'status.json', s)
            return s
        if s['configuration_healthy']: return finish('no_op')
        if not repair: return finish('check_only')
        if s['discord_running']: return finish('defer_running')
        if not allowed(c,s): return finish('blocked_unsafe_shape')
        previous = read_json(c.state/'attempt.json')
        # Global cooldown survives changing settings and separate status checks.
        if previous and c.now()-previous.get('attempted_at',0) < 3600:
            return finish('cooldown')
        if digest(c.cli) != c.cli_sha: return finish('blocked_cli_digest')
        if not stable(c): return finish('defer_update_settling')
        backup = c.state/'backups'/f"guard-{int(c.now())}-{s['fingerprint'][:12]}.tar.gz"
        backup.parent.mkdir(parents=True,exist_ok=True)
        with tarfile.open(backup,'x:gz') as tar:
            for name,p in [('app.asar',c.resources/'app.asar'),('patcher.js',c.dist/'patcher.js'),('renderer.js',c.dist/'renderer.js'),('settings.json',c.settings)]:
                tar.add(p,arcname=name)
        fresh = inspect(c)
        if fresh['discord_running'] or fresh['fingerprint'] != s['fingerprint'] or not allowed(c,fresh) or not stable(c):
            return finish('defer_changed_during_backup')
        original_digest = digest(c.resources/'app.asar')
        bundle = [digest(c.dist/x) for x in ['patcher.js','renderer.js']]
        attempt = {'attempted_at':c.now(),'fingerprint':s['fingerprint'],'result':'started','backup':str(backup),'backup_sha256':digest(backup)}
        save(c.state/'attempt.json',attempt)
        env = os.environ.copy()
        env.update(VENCORD_DEV_INSTALL='1',VENCORD_USER_DATA_DIR=str(c.base))
        try:
            result = c.runner([str(c.cli),'--install',f'--location={c.app}'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
            after = inspect(c)
            ok = result.returncode == 0 and after['configuration_healthy'] and bundle == [digest(c.dist/x) for x in ['patcher.js','renderer.js']] and digest(c.resources/'_app.asar') == original_digest
            attempt['result'] = 'verified' if ok else 'failed_verification'
            attempt['exit_code'] = result.returncode
            s = after
        except (OSError,subprocess.TimeoutExpired) as e:
            attempt['result'] = type(e).__name__
        save(c.state/'attempt.json',attempt)
        s['repair'] = {'attempted':True,**attempt}
        save(c.state/'status.json',s)
        return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repair',action='store_true')
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    try: result=run(Config(),args.repair)
    except Exception as e:
        result={'state':'check_failed','error':type(e).__name__}
        save(Config().state/'status.json',result)
    if args.check: print(json.dumps(result,indent=2))
    return 0 if result.get('configuration_healthy') else 1

if __name__=='__main__': raise SystemExit(main())
