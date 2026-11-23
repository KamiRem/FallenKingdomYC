"""Revue géométrique locale des deux exceptions r2 ; aucune capacité réseau."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from map_reader import Reader
from minestrator_cold_backup import protect_directory, write, now
from v22_rebase_plan import canonical
from terrain_reference import fingerprint, normalized, state

AIR = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))
INITIAL_ARCHIVE_SHA = '75b192b294af5a62d966206014efe957ef6ecfe3926e4a1bfe00d2dea2b1e0ea'


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def inspect_column(reader, at):
    """Mesurer un puits ; ne vaut pas certification générale de sécurité en jeu."""
    x, y, z = at
    if reader.block(x, y, z) not in AIR:
        raise ValueError('ExpectedAirCell')
    bottom, top = y, y
    while bottom > -64 and reader.block(x, bottom - 1, z) in AIR:
        bottom -= 1
    while top < 319 and reader.block(x, top + 1, z) in AIR:
        top += 1
    floor = reader.block(x, bottom - 1, z) if bottom > -64 else None
    rims = []
    for dx, dz in DIRECTIONS:
        rim = next((yy for yy in range(319, bottom - 1, -1)
                    if reader.block(x + dx, yy, z + dz) not in AIR), None)
        if rim is not None:
            rims.append({'offset': [dx, dz], 'at': [x + dx, rim, z + dz],
                         'block': reader.block(x + dx, rim, z + dz),
                         'fallBlocks': rim + 1 - bottom,
                         'unobstructedFromRim': top >= rim + 1})
    hazard = (floor == 'minecraft:stone' and top == 319 and
              any(r['fallBlocks'] >= 4 and r['unobstructedFromRim'] for r in rims))
    return {'at': list(at), 'bottomAir': [x, bottom, z], 'topAir': [x, top, z],
            'floorBlock': floor, 'openToSky': top == 319, 'rims': rims,
            'waterInColumn': False,
            'hazards': ['UNGUARDED_VERTICAL_DROP_ON_STONE'] if hazard else [],
            'requiresInGameInspectionForGeneralSafety': True}


def compare_reference_points(original_reader, proposed_reader, points, defaults, planned):
    differences = []
    if len({tuple(at) for at in points}) != len(points):
        raise ValueError('DuplicateReferencePoint')
    for at in points:
        expected = normalized(state(original_reader, *at), defaults)
        actual = normalized(state(proposed_reader, *at), defaults)
        if actual != expected:
            if tuple(at) in planned:
                raise ValueError('RestorationTargetMismatch')
            differences.append({'at': at, 'approvedInitial': expected, 'preservedCurrent': actual})
    return {'controlledCells': len(points), 'matchingInitialCells': len(points) - len(differences),
            'differences': differences}


def run(work, output):
    parent = (Path.home() / 'FKBackups').resolve()
    work, output = work.resolve(), output.resolve()
    if any(p == parent or not p.is_relative_to(parent) for p in (work, output)):
        raise ValueError('PrivateFolderRequired')
    if output.is_relative_to(work) or work.is_relative_to(output):
        raise ValueError('IndependentOutputRequired')
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    receipt = load(Path(__file__).resolve().parents[1] / 'tests/results/minestrator-v22-preflight-20261123.json')
    for name, expected in receipt['privateEvidenceSha256'].items():
        if sha(work / name) != expected:
            raise ValueError('AuditEvidenceChanged')
    plan = load(work / 'transition-plan-private.json')
    audit = load(work / 'fingerprint-private.json')
    regions = load(work / 'regions-private.json')
    payload = work / plan['payloadDirectory']
    for item in plan['files']:
        if sha(payload / item['path']) != item['newSha256']:
            raise ValueError('ProposedPayloadChanged')
    for name, expected in regions['doubleReadHashes'].items():
        if sha(work / 'region-readback' / name) != expected or audit['doubleReadHashes'][name] != expected:
            raise ValueError('RemoteReadbackChanged')
    delivery = parent / 'V22-FINAL-20261123-02'
    initial = delivery / 'candidate'
    archive = delivery / 'fallenkingdom-v22-final-candidate-private.zip'
    if sha(archive) != INITIAL_ARCHIVE_SHA:
        raise ValueError('ApprovedCandidateArchiveChanged')
    original_reference_name = 'maintenance/new-match-reference-v2.2.json'
    required = {original_reference_name}
    required.update(regions['doubleReadHashes'])
    with zipfile.ZipFile(archive) as z:
        for name in required:
            found = [n for n in z.namelist() if n == name or n.endswith('/' + name)]
            if len(found) != 1 or hashlib.sha256(z.read(found[0])).hexdigest() != sha(initial / name):
                raise ValueError('ApprovedCandidateWorkingCopyChanged')
    original_ref = load(initial / original_reference_name)
    proposed_ref = load(payload / original_reference_name)
    defaults = load(payload / 'maintenance/block-defaults-26.3.json')
    restoration_path = parent / 'V22-VANILLA-20261123-01/restoration-plan-private.json'
    restoration_proof = load(Path(__file__).resolve().parents[1] / 'tests/results/vanilla-underground-20261123.json')
    if sha(restoration_path) != restoration_proof['privateEvidenceSha256']['restoration-plan-private.json']:
        raise ValueError('RestorationPlanChanged')
    restoration = load(restoration_path)
    planned = {tuple(b['at']) for b in restoration['blocks']}
    if len(planned) != 22219 or len(restoration['blocks']) != 22219:
        raise ValueError('UnexpectedRestorationCount')
    initial_reader, proposed_reader = Reader(initial), Reader(payload)
    points = original_ref['underground']['checkPoints']
    if points != proposed_ref['underground']['checkPoints']:
        raise ValueError('ReferenceGeometryChanged')
    if fingerprint(initial_reader, points, defaults) != original_ref['underground']['blockStatesSha256']:
        raise ValueError('InitialReferenceMismatch')
    comparison = compare_reference_points(initial_reader, proposed_reader, points, defaults, planned)
    if comparison['controlledCells'] != 37128 or comparison['matchingInitialCells'] != 37126:
        raise ValueError('UnexpectedReferenceDifferenceCount')
    if comparison['differences'] != proposed_ref['underground']['proposedPreservedCurrentEdits']:
        raise ValueError('UndocumentedReferenceException')
    if fingerprint(proposed_reader, points, defaults) != proposed_ref['underground']['blockStatesSha256']:
        raise ValueError('ProposedReferenceMismatch')
    current_reader = Reader(work / 'region-readback')
    for block in restoration['blocks']:
        if normalized(state(current_reader, *block['at']), defaults) != canonical(block['before'], defaults):
            raise ValueError('UnexpectedSourceRestorationCell')
        if normalized(state(proposed_reader, *block['at']), defaults) != canonical(block['after'], defaults):
            raise ValueError('RestorationTargetMismatch')
    cells = []
    for difference in comparison['differences']:
        at = difference['at']
        if difference['approvedInitial'] != normalized({'Name': 'minecraft:stone'}, defaults) or difference['preservedCurrent'] != normalized({'Name': 'minecraft:air'}, defaults):
            raise ValueError('UnexpectedExceptionState')
        if current_reader.block(*at) != 'minecraft:air':
            raise ValueError('SourceExceptionNotAir')
        column = inspect_column(proposed_reader, at)
        column['currentBeforeRestoration'] = inspect_column(current_reader, at)
        x, _, z = at
        column['insideTeamTerritories'] = [b['team'] for b in original_ref['bases']
            if (x-float(b['center']['X']))**2+(z-float(b['center']['Z']))**2 <= b['radius']**2]
        column['outsideRestorationTargets'] = tuple(at) not in planned
        cells.append(column)
    a, b = (v['at'] for v in cells)
    stacked = a[0] == b[0] and a[2] == b[2] and abs(a[1] - b[1]) == 1
    point_set = {tuple(at) for at in points}
    column_differences = []
    if stacked:
        x, _, z = a
        for yy in range(max(a[1], b[1]) + 1, 320):
            expected = normalized(state(initial_reader, x, yy, z), defaults)
            actual = normalized(state(proposed_reader, x, yy, z), defaults)
            if expected != actual:
                column_differences.append({'at': [x, yy, z], 'approvedInitial': expected,
                                           'preservedCurrent': actual,
                                           'insideControlledFootprint': (x, yy, z) in point_set})
    hazards = sorted({h for c in cells for h in c['hazards']})
    report = {'operation': output.name, 'createdAtUtc': now(), 'sourceObservationFinishedAtUtc': regions['finishedAtUtc'],
              'remoteAccessDuringReview': False, 'remoteWritesPerformed': False,
              'backupStarted': False, 'referenceR2Approved': False,
              'conditionalApprovalSafetyGatePassed': False, 'exceptionsStacked': stacked,
              'restorationTargetsVerified': len(planned), 'originalReferenceArchiveSha256': INITIAL_ARCHIVE_SHA,
              'sourceAuditSha256': sha(work / 'fingerprint-private.json'),
              'sourceRegionsEvidenceSha256': sha(work / 'regions-private.json'),
              'sourceTransitionPlanSha256': sha(work / 'transition-plan-private.json'),
              'comparison': comparison, 'cells': cells, 'hazards': hazards,
              'columnDifferencesAboveExceptions': column_differences,
              'inGameInspectionPerformed': False,
              'outcome': 'BLOCKED_TERRAIN_SAFETY' if hazards else 'REQUIRES_ADDITIONAL_SAFETY_REVIEW'}
    # Aucun chemin de ce diagnostic n'approuve une référence ou n'engage une sauvegarde.
    for name, expected in receipt['privateEvidenceSha256'].items():
        if sha(work / name) != expected:
            raise ValueError('AuditEvidenceChangedDuringReview')
    for item in plan['files']:
        if sha(payload / item['path']) != item['newSha256']:
            raise ValueError('ProposedPayloadChangedDuringReview')
    report['originalEvidenceAndProposedPayloadUnchanged'] = True
    protect_directory(output)
    write(output / 'cell-safety-review-private.json', report)
    print(json.dumps({'outcome': report['outcome'], 'referenceR2Approved': False, 'backupStarted': False,
        'controlledCells': comparison['controlledCells'], 'matchingInitialCells': comparison['matchingInitialCells'],
        'exceptions': len(cells), 'restorationTargetsVerified': len(planned),
        'exceptionsStacked': stacked, 'hazards': hazards,
        'fallBlocks': sorted({r['fallBlocks'] for c in cells for r in c['rims']}),
        'columnDifferencesAboveExceptionsOutsideFootprint': sum(not d['insideControlledFootprint'] for d in column_differences),
        'insideTeamTerritory': any(c['insideTeamTerritories'] for c in cells)}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.work, args.output)
    except Exception as error:
        print(json.dumps({'outcome': 'REVIEW_FAILED', 'reason': type(error).__name__, 'detail': str(error)}))
        sys.exit(1)
    sys.exit(2 if result['hazards'] else 3)
