"""Standard-library-only CLI for the independently written pure_lib3mf.

Usage:
    python check_3mf.py file.3mf
    python check_3mf.py --intersections a.3mf b.3mf
    python check_3mf.py --max-pairs 100000 file.3mf

Returns exit status 0 on successful checks, 1 for invalid geometry/package.
The checker is NOT a full official XSD/ISO conformance verifier.
"""
import argparse
import json
import os
import sys
import lib3mf


def main(argv=None):
    parser=argparse.ArgumentParser(description='Check 3MF package structure and meshes')
    parser.add_argument('files',nargs='+')
    parser.add_argument('--intersections',action='store_true',help='Run pairwise triangle intersection checks')
    parser.add_argument('--max-pairs',type=int,default=200000)
    parser.add_argument('--no-geometry',action='store_true')
    args=parser.parse_args(argv)
    status=0
    for name in args.files:
        try:
            with open(name,'rb') as f:data=f.read()
            report=lib3mf.Check3MFPackage(data,geometry=not args.no_geometry,
                    check_self_intersections=args.intersections,max_pairs=args.max_pairs)
            result=report.to_dict()
            if not report.ok: status=1
        except Exception as exc:
            result={'ok':False,'issues':[{'severity':'error','code':'read_error','message':str(exc)}]}
            status=1
        result['file']=os.fspath(name)
        print(json.dumps(result,indent=2,sort_keys=True))
    return status


if __name__=='__main__':
    sys.exit(main())
