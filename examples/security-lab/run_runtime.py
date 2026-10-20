#!/usr/bin/env python3
"""Run bounded no-actuator DDS cases. Requires sourced Jazzy and two separately provisioned lab keystores."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keystore',type=Path,required=True)
    parser.add_argument('--untrusted-keystore',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if os.environ.get('ROS_DISTRO')!='jazzy':parser.error('Source ROS Jazzy first')
    args.output.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy();env.update({'RMW_IMPLEMENTATION':'rmw_fastrtps_cpp','ROS_DOMAIN_ID':'42','ROS_AUTOMATIC_DISCOVERY_RANGE':'LOCALHOST','ROS_SECURITY_ENABLE':'true','ROS_SECURITY_STRATEGY':'Enforce','ROS_SECURITY_KEYSTORE':str(args.keystore.resolve())})
    env.pop('ROS_SECURITY_ENCLAVE_OVERRIDE',None)
    subprocess.run([sys.executable,str(HERE/'capture_versions.py')],env=env,stdout=(args.output/'versions.json').open('w'),check=True)
    cases=[]
    def stop(process):
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
    def command(role,enclave=None,extra=None):
        return ['ros2','run','demo_nodes_cpp',role,'--ros-args','--enclave',enclave or '/security_lab/'+role]+(extra or [])
    def single(identifier,cmd):
        path=args.output/(identifier+'.log')
        with path.open('w') as out:
            p=subprocess.Popen(cmd,env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
            ended=True
            try:p.wait(timeout=8)
            except subprocess.TimeoutExpired:ended=False;stop(p)
        text=path.read_text(errors='replace')
        return {'id':identifier,'command':cmd,'exit_status':p.returncode,'ended_without_test_shutdown':ended,'evidence_paths':[path.name]},text
    def pair(identifier,other_keystore=None):
        processes=[];paths=[];start=time.monotonic()
        other=env.copy()
        if other_keystore:other['ROS_SECURITY_KEYSTORE']=str(other_keystore.resolve())
        try:
            for role,settings in [('listener',other),('talker',env)]:
                path=args.output/(identifier+'-'+role+'.log');out=path.open('w');paths.append(path)
                p=subprocess.Popen(command(role),env=settings,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
                out.close();processes.append(p)
            time.sleep(8)
            running=all(p.poll() is None for p in processes)
        finally:
            for p in processes:stop(p)
        texts=[p.read_text(errors='replace') for p in paths]
        delivered=texts[0].count('I heard:')
        published=texts[1].count('Publishing:')
        return {'id':identifier,'observation_window_seconds':round(time.monotonic()-start,2),'participants_running_at_end_of_window':running,'received_messages':delivered,'published_messages':published,'evidence_paths':[p.name for p in paths]},texts
    case,_=pair('authorized');case['outcome']='pass' if case['received_messages']>=3 and case['published_messages']>=3 and case['participants_running_at_end_of_window'] else 'fail';cases.append(case)
    for identifier,cmd in [('missing-enclave',command('talker','/security_lab/missing')),('forbidden-remap',command('talker',extra=['--remap','chatter:=not_chatter'])),('wrong-profile',command('talker','/security_lab/listener'))]:
        case,text=single(identifier,cmd)
        case['outcome']='pass' if case['ended_without_test_shutdown'] and case['exit_status']!=0 and 'Publishing:' not in text and any(term in text.lower() for term in ['security','permission','denied','secure']) else 'fail'
        cases.append(case)
    case,text=single('listener-publish-probe',[sys.executable,str(HERE/'probe_publish.py'),'--ros-args','--enclave','/security_lab/listener'])
    case['outcome']='pass' if case['ended_without_test_shutdown'] and case['exit_status']==2 and 'NODE_READY' in text and '"publisher_created": false' in text else 'fail';cases.append(case)
    case,texts=pair('untrusted-authority',args.untrusted_keystore)
    case['outcome']='pass' if case['participants_running_at_end_of_window'] and case['received_messages']==0 and case['published_messages']>=3 and any(term in '\n'.join(texts).lower() for term in ['authenticate','authentication','verify','certificate','handshake','identity']) else 'inconclusive';cases.append(case)
    case,_=pair('authorized-after-negative-cases');case['outcome']='pass' if case['received_messages']>=3 and case['published_messages']>=3 and case['participants_running_at_end_of_window'] else 'fail';cases.append(case)
    artifacts=[];key_modes=[]
    for role in ['talker','listener']:
        directory=args.keystore/'enclaves/security_lab'/role
        for filename in ['cert.pem','governance.p7s','permissions.p7s','governance.xml','permissions.xml']:
            path=directory/filename
            if path.exists():
                artifacts.append({'enclave':role,'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
                if filename.endswith('.xml'):(args.output/(role+'-'+filename)).write_bytes(path.read_bytes())
        path=directory/'key.pem';key_modes.append({'enclave':role,'mode':oct(path.stat().st_mode & 0o777),'no_group_or_other_access':not bool(path.stat().st_mode & 0o077)})
    result={'status':'runtime-observed','baseline':'Ubuntu Noble userspace / ROS 2 Jazzy / rmw_fastrtps_cpp','settings':{k:env[k] for k in ['RMW_IMPLEMENTATION','ROS_DOMAIN_ID','ROS_AUTOMATIC_DISCOVERY_RANGE','ROS_SECURITY_ENABLE','ROS_SECURITY_STRATEGY']},'cases':cases,'runtime_artifact_hashes':artifacts,'key_file_modes':key_modes,'private_keys_exported':False,'physical_robot_tested':False,'limitations':['No actuator or physical robot was attached.','No packet-level confidentiality measurement was performed.','Filesystem modes do not prove isolation from privileged or same-process code.','Revocation, expiration, hardware-backed keys and load behavior were not tested.']}
    (args.output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cases':[{k:r[k] for k in ['id','outcome']} for r in cases],'all_passed':all(c['outcome']=='pass' for c in cases)},indent=2))
    if not all(c['outcome']=='pass' for c in cases):raise SystemExit(1)

if __name__=='__main__':main()
