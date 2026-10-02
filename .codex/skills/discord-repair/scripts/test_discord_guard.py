import unittest, tempfile, json, sys, subprocess, struct
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).parent))
from discord_guard import Config, run, digest, running
from unittest.mock import patch

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); root=Path(self.tmp.name)
        self.c=Config(app=root/'Discord.app',base=root/'Vencord',dist=root/'custom-dist',state=root/'state',cli=root/'cli',process=lambda:False,stability=0)
        c=self.c;c.resources.mkdir(parents=True);c.dist.mkdir();c.base.mkdir();(c.base/'dist').symlink_to(c.dist)
        (c.base/'settings').mkdir();c.settings.write_text(json.dumps({'plugins':{x:{'enabled':True} for x in ['AutoStream','AquaMuteSync']}}))
        (c.dist/'patcher.js').write_text('custom patcher');(c.dist/'renderer.js').write_text('AutoStream AquaMuteSync')
        c.cli.write_text('fixture cli');c.cli_sha=digest(c.cli)
        package = b'{"name":"discord","main":"index.js"}'
        content = b'console.log("fixture");'
        header = json.dumps({'files':{'package.json':{'size':len(package),'offset':'0'},'index.js':{'size':len(content),'offset':str(len(package))}}},separators=(',',':')).encode()
        padded = header + b'\x00' * ((-len(header)) % 4)
        (c.resources/'app.asar').write_bytes(struct.pack('<4I',4,len(padded)+8,len(padded)+4,len(header))+padded+package+content)
        self.calls=[]
        def invoke(*args,**kwargs): self.calls.append((args,kwargs));return SimpleNamespace(returncode=0)
        c.runner=invoke
    def tearDown(self):self.tmp.cleanup()
    def patch(self):
        c=self.c;(c.resources/'app.asar').rename(c.resources/'_app.asar')
        (c.resources/'app.asar').write_text('require('+json.dumps(str(c.base/'dist/patcher.js'))+')')
    def test_healthy_noop(self):
        self.patch();s=run(self.c,True);self.assertTrue(s['configuration_healthy']);self.assertEqual(self.calls,[])
    def test_running_deferred(self):
        self.c.process=lambda:True;self.assertEqual(run(self.c,True)['repair']['result'],'defer_running');self.assertFalse(self.calls)
    def test_missing_plugin_blocked(self):
        (self.c.dist/'renderer.js').write_text('AutoStream');run(self.c,True);self.assertFalse(self.calls)
    def test_missing_patcher_blocked(self):
        (self.c.dist/'patcher.js').unlink();run(self.c,True);self.assertFalse(self.calls)
    def test_disabled_plugin_blocked(self):
        self.c.settings.write_text('{}');run(self.c,True);self.assertFalse(self.calls)
    def test_stale_original_blocked(self):
        (self.c.resources/'_app.asar').write_text('old discord');run(self.c,True);self.assertFalse(self.calls)
    def test_wrong_dist_blocked(self):
        (self.c.base/'dist').unlink();run(self.c,True);self.assertFalse(self.calls)
    def test_recent_update_deferred(self):
        self.c.stability=60;self.assertEqual(run(self.c,True)['repair']['result'],'defer_update_settling');self.assertFalse(self.calls)
    def test_cli_digest_blocked(self):
        self.c.cli_sha='wrong';run(self.c,True);self.assertFalse(self.calls)
    def test_false_success_and_cooldown_survive_checks(self):
        self.assertEqual(run(self.c,True)['repair']['result'],'failed_verification')
        run(self.c);self.assertEqual(run(self.c,True)['repair']['result'],'cooldown');self.assertEqual(run(self.c,True)['repair']['result'],'cooldown');self.assertEqual(len(self.calls),1)
    def test_process_starts_during_backup(self):
        states=iter([False,True]);self.c.process=lambda:next(states);run(self.c,True);self.assertFalse(self.calls)
    def test_verified_repair(self):
        def invoke(*a,**kw):
            self.assertEqual(kw['env']['VENCORD_DEV_INSTALL'],'1');self.assertEqual(kw['env']['VENCORD_USER_DATA_DIR'],str(self.c.base));self.patch();return SimpleNamespace(returncode=0)
        self.c.runner=invoke;s=run(self.c,True);self.assertEqual(s['repair']['result'],'verified');self.assertTrue(s['configuration_healthy'])
    def test_changed_original_fails(self):
        def invoke(*a,**kw):self.patch();(self.c.resources/'_app.asar').write_text('wrong original');return SimpleNamespace(returncode=0)
        self.c.runner=invoke;self.assertEqual(run(self.c,True)['repair']['result'],'failed_verification')
    def test_external_updater_defers(self):
        self.c.process=None
        with patch('discord_guard.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='/Users/example/Library/Caches/com.hnc.Discord.ShipIt/ShipIt')):
            self.assertTrue(running(self.c))
    def test_unknown_process_state_defers(self):
        self.c.process=None
        with patch('discord_guard.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')):
            self.assertTrue(running(self.c))
    def test_truncated_archive_blocked(self):
        (self.c.resources/'app.asar').write_bytes(b'x')
        self.assertEqual(run(self.c,True)['repair']['result'],'blocked_unsafe_shape');self.assertFalse(self.calls)
    def test_actual_cli_integration(self):
        from discord_guard import CLI,CLI_SHA
        self.c.cli=CLI;self.c.cli_sha=CLI_SHA;self.c.runner=subprocess.run
        s=run(self.c,True);self.assertEqual(s['repair']['result'],'verified');self.assertTrue(s['configuration_healthy'])

if __name__=='__main__':unittest.main()
