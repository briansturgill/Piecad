#!/usr/bin/env python3
"""Run the 3MF Consortium conformance corpus against the local pure-Python lib3mf.

Python standard library only. This is a *regression and compatibility harness*,
NOT the 3MF Consortium's official conformance verifier or an XSD validator.

Install corpus separately: https://github.com/3MFConsortium/test_suites

Examples (run with lib3mf.py in the same directory):
    python test_3mf_conformance.py /path/to/test_suites
    python test_3mf_conformance.py /path/to/test_suites.zip --suites 3,5,6
    python test_3mf_conformance.py /path/to/test_suites --roundtrip rewrite \
        --json results.json --csv results.csv
    python test_3mf_conformance.py /path/to/test_suites/suite3_core --limit 20 -v
    python test_3mf_conformance.py /path/to/a.3mf --roundtrip rewrite

Suite input can be an extracted directory, a ZIP of the entire repository,
its subdirectory, or an individual .3mf file. Cases are labeled by the
positive_test_cases / negative_test_cases directory names. An individual .3mf
is assumed positive unless --standalone-expect negative is specified.

Exit status: 0 = no failures; 1 = one or more failures; 2 = usage/input error;
3 = all selected cases were skipped (or none matched).

Known unsupported suites 1,4,7,8,10,11 are SKIP by default (not counted as
passing), even if the reader happens to accept them. Use --include-unsupported
to measure actual behavior on these suites without claiming support.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Iterator
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

try:
    import lib3mf
except ImportError as exc:
    raise SystemExit('Cannot import lib3mf. Put this file alongside lib3mf.py, '
                     'or add its directory to PYTHONPATH.') from exc

# This module implements core, a subset of production, and the principal
# materials resource types. The other suite combinations are *not* supported.
SUITES = {
    1: 'core + slice + production',
    2: 'core + production + materials',
    3: 'core',
    4: 'core + slice',
    5: 'core + production',
    6: 'core + materials',
    7: 'core + beam lattice',
    8: 'core + production + secure content',
    9: 'core with extensions',
    10: 'core + boolean operations',
    11: 'core + displacement',
}
UNSUPPORTED_SUITES = {1, 4, 7, 8, 10, 11}
SUPPORTED_REQUIRED_NS = {
    'http://schemas.microsoft.com/3dmanufacturing/core/2015/02',
    'http://schemas.microsoft.com/3dmanufacturing/material/2015/02',
    'http://schemas.microsoft.com/3dmanufacturing/production/2015/06',
}
CASE_DIRS = {
    'positive_test_cases': 'positive',
    'negative_test_cases': 'negative',
    'positive-test-cases': 'positive',
    'negative-test-cases': 'negative',
}
METADATA_MARKER = 'PurePythonLib3MFConformanceRoundtripMarker'
METADATA_NAMESPACE = 'urn:piecad:3mf-conformance'


@dataclass(frozen=True)
class Case:
    source: Path
    member: str | None
    name: str
    suite: int | None
    expected: str
    size: int


@dataclass
class Result:
    case: str
    suite: str
    expected: str
    status: str
    read_ok: bool | None = None
    package_ok: bool | None = None
    roundtrip_ok: bool | None = None
    file_bytes: int = 0
    elapsed_seconds: float = 0.0
    note: str = ''
    model_meshes: int | None = None
    model_triangles: int | None = None


def _suite_number(name: str) -> int | None:
    for part in Path(name.replace('\\', '/')).parts:
        match = re.match(r'^suite(\d+)(?:[_-]|$)', part, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _expectation(name: str, standalone: str) -> str:
    for part in name.replace('\\', '/').lower().split('/'):
        if part in CASE_DIRS:
            return CASE_DIRS[part]
    return standalone


def _discover(inputs: list[Path], standalone: str) -> Iterator[Case]:
    """Yield cases without extracting repository ZIPs."""
    for src in inputs:
        if src.is_dir():
            for p in sorted(src.rglob('*')):
                if p.is_file() and p.suffix.lower() == '.3mf':
                    # Include parent name for directories directly inside suites.
                    relative = p.relative_to(src).as_posix()
                    display = str(src.name) + '/' + relative
                    yield Case(p, None, display, _suite_number(display),
                               _expectation(display, standalone), p.stat().st_size)
        elif src.is_file() and src.suffix.lower() == '.3mf':
            yield Case(src, None, src.name, _suite_number(str(src)),
                       _expectation(str(src), standalone), src.stat().st_size)
        elif src.is_file() and src.suffix.lower() == '.zip':
            try:
                with ZipFile(src) as archive:
                    entries = sorted(archive.infolist(), key=lambda x: x.filename)
                    for item in entries:
                        if item.is_dir() or not item.filename.lower().endswith('.3mf'):
                            continue
                        name = item.filename
                        yield Case(src, name, name, _suite_number(name),
                                   _expectation(name, standalone), item.file_size)
            except BadZipFile as ex:
                raise ValueError(f'Invalid corpus ZIP: {src}: {ex}') from ex
        else:
            raise ValueError(f'Input not found or not a directory, .zip or .3mf: {src}')


def _read_bytes(case: Case) -> bytes:
    if case.member is None:
        return case.source.read_bytes()
    with ZipFile(case.source) as zf:
        return zf.read(case.member)


def _required_unknown_namespaces(data: bytes) -> set[str]:
    """Detect *declared required* extensions only (not optional vendor data).

    Best-effort classification to avoid claiming a feature is supported simply
    because the parser ignores its XML elements. Does not validate the XML.
    """
    result: set[str] = set()
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            for name in archive.namelist():
                if not name.lower().endswith('.model'):
                    continue
                namespace_map: dict[str, str] = {}
                root = None
                for event, value in ET.iterparse(io.BytesIO(archive.read(name)),
                                                 events=('start-ns', 'start')):
                    if event == 'start-ns':
                        prefix, uri = value
                        namespace_map[prefix or ''] = uri
                    elif root is None:
                        root = value
                        break
                if root is None:
                    continue
                for key, value in root.attrib.items():
                    if key.rsplit('}', 1)[-1].lower() != 'requiredextensions':
                        continue
                    for prefix in value.split():
                        uri = namespace_map.get(prefix)
                        if uri is None:
                            result.add(f'unbound prefix {prefix}')
                        elif uri not in SUPPORTED_REQUIRED_NS:
                            result.add(uri)
    except (BadZipFile, KeyError, ET.ParseError, OSError):
        # Let the normal reader/checker classify corrupt or malformed packages.
        pass
    return result


def _sha(obj: object) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _geometry_signature(model) -> tuple[str, int, int]:
    """Digest the modeled geometry/build structure, ignoring serialization details.

    A complete full-spec semantic-equivalence checker would require support
    for *all* extensions. We compare the subset this implementation exposes.
    """
    mesh_rows = []
    for mesh in model.GetMeshObjects():
        mesh_rows.append({
            'id': mesh.GetResourceID(),
            'part': mesh.GetPackagePath(),
            'name': mesh.GetName(),
            'vertices': [list(v.Coordinates) for v in mesh.GetVertices()],
            'triangles': [list(t.Indices) for t in mesh.GetTriangleIndices()],
            'object_property': mesh.GetObjectLevelProperty(),
            'triangle_properties': [
                [p.ResourceID, p.PropertyIDs]
                for p in mesh.GetAllTriangleProperties()
            ],
        })
    components = []
    for obj in model.GetComponentsObjects():
        components.append({
            'id': obj.GetResourceID(),
            'part': obj.GetPackagePath(),
            'members': [
                (obj.GetComponent(i).GetObjectResourceID(),
                 obj.GetComponent(i).GetTransform().Fields)
                for i in range(obj.GetComponentCount())
            ],
        })
    build = [(b.GetObjectResourceID(), b.GetObjectTransform().Fields,
              b.GetPartNumber()) for b in model.GetBuildItems()]
    signature = {'unit': int(model.GetUnit()), 'meshes': mesh_rows,
                 'components': components, 'build': build}
    return _sha(signature), len(mesh_rows), sum(len(m['triangles']) for m in mesh_rows)


def _unrelated_zip_bytes_preserved(original: bytes, rewritten: bytes,
                                   model_parts: set[str]) -> list[str]:
    """Compare opaque parts, not the .model files or rebuilt OPC wiring."""
    with ZipFile(io.BytesIO(original)) as a, ZipFile(io.BytesIO(rewritten)) as b:
        original_parts = set(a.namelist())
        new_parts = set(b.namelist())
        changes = []
        for part in original_parts | new_parts:
            if part in model_parts or part.lower().endswith('.rels') or part == '[Content_Types].xml':
                continue
            if part not in original_parts or part not in new_parts:
                changes.append(f'added/removed part: {part}')
            elif a.read(part) != b.read(part):
                changes.append(f'changed opaque part: {part}')
        return changes


def _force_serialization(model) -> None:
    """Edit root metadata only: must cause serialization without changing mesh."""
    group = model.GetMetaDataGroup()
    names = {group.GetMetaData(i).GetName()
             for i in range(group.GetMetaDataCount())}
    name = METADATA_MARKER
    counter = 1
    while name in names:
        counter += 1
        name = f'{METADATA_MARKER}{counter}'
    group.AddMetaData(METADATA_NAMESPACE, name, 'roundtrip')


def _run_one(case: Case, args) -> Result:
    now = perf_counter()
    res = Result(case.name, f'suite{case.suite}' if case.suite is not None else 'standalone',
                 case.expected, 'FAIL', file_bytes=case.size)
    try:
        if case.size > args.max_bytes:
            res.status, res.note = 'SKIP', f'file exceeds --max-bytes={args.max_bytes}'
            return res
        if (case.suite in UNSUPPORTED_SUITES and not args.include_unsupported):
            res.status, res.note = 'SKIP', f'unsupported suite: {SUITES.get(case.suite)}'
            return res
        data = _read_bytes(case)
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            res.status, res.note = 'SKIP', 'Git LFS pointer instead of .3mf; run git lfs pull'
            return res
        unknown = _required_unknown_namespaces(data)
        if unknown and case.expected != 'negative' and not args.include_unsupported:
            res.status, res.note = 'SKIP', 'required extension not implemented: ' + ', '.join(sorted(unknown))
            return res
        wrapper = lib3mf.get_wrapper()
        model = wrapper.CreateModel()
        try:
            reader = model.QueryReader('3mf')
            reader.SetStrictModeActive(args.strict_reader)
            reader.ReadFromBuffer(data)
            res.read_ok = True
        except Exception as ex:  # intentionally capture parser failures per test
            res.read_ok = False
            read_error = f'{type(ex).__name__}: {ex}'
        try:
            report = lib3mf.Check3MFPackage(data, geometry=False)
            res.package_ok = bool(report.ok)
            errors = [f'{i.code}: {i.message}' for i in report.issues
                      if i.severity == 'error']
            package_error = '; '.join(errors[:3])
        except Exception as ex:
            res.package_ok = False
            package_error = f'checker error: {type(ex).__name__}: {ex}'

        # A negative test passes if *either* the reader OR the package checker
        # detects the intentionally invalid input. Geometry checks are used
        # only for negative cases, not as a full printer conformance check.
        if case.expected == 'negative':
            rejected = (res.read_ok is False or res.package_ok is False)
            if not rejected:
                geometry = model.Validate()
                errors = [f'{issue.code}: {issue.message}'
                          for mesh in geometry.values() for issue in mesh.issues
                          if issue.severity == 'error']
                if errors:
                    res.status, res.note = 'PASS', '; '.join(errors[:3])
                    return res
            res.status = 'PASS' if rejected else 'FAIL'
            res.note = (read_error if not res.read_ok else package_error) if rejected else \
                       'negative test was accepted by both reader and checker'
            return res
        if not res.read_ok or not res.package_ok:
            res.note = (read_error if not res.read_ok else '')
            if not res.package_ok:
                res.note += ('; ' if res.note else '') + package_error
            return res
        try:
            original_digest, res.model_meshes, res.model_triangles = _geometry_signature(model)
            if args.roundtrip != 'none':
                if args.roundtrip == 'rewrite':
                    _force_serialization(model)
                saved = model.QueryWriter('3mf').WriteToBuffer()
                if args.roundtrip == 'rewrite' and saved == data:
                    raise AssertionError('writer returned identical bytes despite metadata edit')
                if args.roundtrip == 'copy' and saved != data:
                    raise AssertionError('unmodified imported package was not byte-identical')
                model2 = wrapper.CreateModel()
                model2.QueryReader('3mf').ReadFromBuffer(saved)
                saved_report = lib3mf.Check3MFPackage(saved, geometry=False)
                if not saved_report.ok:
                    raise AssertionError('rewritten package structural validation failed: ' +
                                         ', '.join(i.code for i in saved_report.issues
                                                   if i.severity == 'error'))
                loaded_digest, _, _ = _geometry_signature(model2)
                if loaded_digest != original_digest:
                    raise AssertionError('round-trip changed exposed geometry/build/material assignments')
                lost = _unrelated_zip_bytes_preserved(data, saved, set(model._original_parts))
                if lost:
                    raise AssertionError('; '.join(lost[:3]))
                if args.roundtrip == 'rewrite':
                    metadata = model2.GetMetaDataGroup()
                    if not any(metadata.GetMetaData(i).GetName().startswith(METADATA_MARKER)
                               and metadata.GetMetaData(i).GetNameSpace() == METADATA_NAMESPACE
                               for i in range(metadata.GetMetaDataCount())):
                        raise AssertionError('metadata edit did not survive rewriting')
                res.roundtrip_ok = True
            res.status = 'PASS'
            res.note = f'{res.model_meshes} meshes, {res.model_triangles} triangles'
        except Exception as ex:
            res.roundtrip_ok = False if args.roundtrip != 'none' else None
            res.note = f'{type(ex).__name__}: {ex}'
    except (OSError, BadZipFile, ValueError) as ex:
        res.note = f'{type(ex).__name__}: {ex}'
    finally:
        res.elapsed_seconds = round(perf_counter() - now, 5)
    return res


def _parse_suites(s: str) -> set[int] | None:
    if s.strip().lower() == 'all':
        return None
    try:
        result = {int(item.strip().removeprefix('suite'))
                  for item in s.lower().split(',')}
        if not result or any(i not in SUITES for i in result):
            raise ValueError
        return result
    except ValueError as ex:
        raise argparse.ArgumentTypeError('use --suites all or numbers like 2,3,5,6') from ex


def _write_json(path: Path, items: list[Result], elapsed: float) -> None:
    payload = {
        'harness': 'pure_lib3mf conformance regression runner',
        'lib3mf_version': getattr(lib3mf, '__version__', 'unknown'),
        'independent_conformance_verifier': False,
        'elapsed_seconds': round(elapsed, 3),
        'summary': dict(Counter(r.status for r in items)),
        'cases': [asdict(r) for r in items],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


def _write_csv(path: Path, items: list[Result]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as file:
        fields = list(Result.__dataclass_fields__)
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(item) for item in items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Test pure lib3mf against the official 3MF Consortium test_suites corpus.')
    parser.add_argument('paths', nargs='+', type=Path,
                        help='test_suites directory, source ZIP, suite subdirectory or .3mf file')
    parser.add_argument('--suites', default='all', type=_parse_suites,
                        metavar='N,N', help='suite numbers, e.g. 2,3,5,6 (default: all)')
    parser.add_argument('--roundtrip', choices=('none', 'copy', 'rewrite'), default='rewrite',
                        help='none: read/check; copy: unmodified save; rewrite: metadata edit/save (default)')
    parser.add_argument('--include-unsupported', action='store_true',
                        help='attempt known-unsupported suite/required-extension tests instead of skipping')
    parser.add_argument('--strict-reader', action='store_true',
                        help='enable strict Reader warnings rejection')
    parser.add_argument('--standalone-expect', choices=('positive', 'negative'), default='positive',
                        help='expected outcome when no positive/negative directory label exists')
    parser.add_argument('--match', default='', help='substring match on case paths (case insensitive)')
    parser.add_argument('--limit', type=int, default=0,
                        help='stop after this many selected cases (0 = unlimited)')
    parser.add_argument('--max-bytes', type=int, default=200 * 1024 * 1024,
                        help='skip oversized individual 3MF files (default 200 MiB)')
    parser.add_argument('--json', type=Path, help='write full JSON results to path')
    parser.add_argument('--csv', type=Path, help='write full CSV results to path')
    parser.add_argument('--verbose', '-v', action='store_true', help='print every case, including passes')
    parser.add_argument('--list', action='store_true', help='list cases without running them')
    args = parser.parse_args(argv)

    if args.limit < 0 or args.max_bytes < 1:
        parser.error('--limit must be >= 0 and --max-bytes must be > 0')
    start = perf_counter()
    try:
        cases = sorted(_discover(args.paths, args.standalone_expect),
                       key=lambda c: (c.suite or 0, c.name))
    except (ValueError, OSError, BadZipFile) as ex:
        parser.error(str(ex))
    selected = [c for c in cases
                if (args.suites is None or c.suite in args.suites)
                and args.match.lower() in c.name.lower()]
    if args.limit:
        selected = selected[:args.limit]
    if not selected:
        print('No matching .3mf files. Check the corpus path and --suites/--match filters.', file=sys.stderr)
        return 3
    if args.list:
        for c in selected:
            print(f'{c.expected:8} suite{c.suite or "?":<3} {c.name}')
        print(f'{len(selected)} cases listed')
        return 0
    print(f'pure_lib3mf {getattr(lib3mf, "__version__", "unknown")} | '
          f'{len(selected)} cases | roundtrip={args.roundtrip} | '
          f'unsupported={"attempt" if args.include_unsupported else "skip"}')
    results: list[Result] = []
    for idx, case in enumerate(selected, 1):
        result = _run_one(case, args)
        results.append(result)
        if args.verbose or result.status == 'FAIL':
            print(f'[{idx:5}/{len(selected)}] {result.status:4} '
                  f'{result.expected:8} {result.case}\n'
                  f'    {result.note[:320]}')
    print('\nPer-suite results (PASS / FAIL / SKIP):')
    groups: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        groups[r.suite][r.status] += 1
    for name in sorted(groups, key=lambda n: int(n[5:]) if n.startswith('suite') else 0):
        c = groups[name]
        print(f'{name:12} {c["PASS"]:5} / {c["FAIL"]:5} / {c["SKIP"]:5}')
    total = Counter(r.status for r in results)
    print(f'TOTAL        {total["PASS"]:5} / {total["FAIL"]:5} / {total["SKIP"]:5} '
          f'({perf_counter()-start:.2f}s)')
    if args.json:
        _write_json(args.json, results, perf_counter() - start)
        print(f'JSON: {args.json}')
    if args.csv:
        _write_csv(args.csv, results)
        print(f'CSV: {args.csv}')
    if total['FAIL']:
        return 1
    if not total['PASS']:
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
