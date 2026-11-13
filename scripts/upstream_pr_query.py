#!/usr/bin/env python3
"""Query an explicit local PR discovery index; never fetch sources or run commands.

The index is a navigation aid, separate from the project's measured case cards.
Metadata verification, diff review and target reproduction are distinct facts.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'skills/key-operator-opt/references/upstream-pr-index.json'
REVIEW_LEVELS = ('discovery', 'diff_reviewed', 'target_reproduced')
CLAIM_SCOPE = 'historical_navigation_only; no current dispatch, correctness or performance claim'
SOURCE_KINDS = {'discovery_document', 'local_record', 'upstream_metadata',
                'upstream_diff', 'target_evidence'}
COMMIT = re.compile(r'[0-9a-f]{40}')
SLUG = re.compile(r'[a-z0-9][a-z0-9_-]*')
REPOSITORY = re.compile(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*')


def _fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f'{label} must contain exactly: {", ".join(sorted(fields))}')


def _text(value, label):
    if (not isinstance(value, str) or not value.strip()
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError(f'{label} must be nonempty text without control characters')
    return value


def _texts(value, label, *, empty=False):
    if not isinstance(value, list) or (not empty and not value):
        raise ValueError(f'{label} must be a {"possibly empty" if empty else "nonempty"} list')
    for item in value:
        _text(item, label)
    if len(set(value)) != len(value):
        raise ValueError(f'{label} contains duplicates')


def _day(value, label, *, nullable=False):
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError(f'{label} must be an ISO date')
    result = date.fromisoformat(value)
    if result < date(2008, 1, 1):
        raise ValueError(f'{label} predates GitHub')
    return result


def _commit(value, label, *, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not COMMIT.fullmatch(value):
        raise ValueError(f'{label} must be a full lowercase 40-character commit SHA')


def _source(card, updated):
    _fields(card, {'id', 'kind', 'location', 'revision', 'audited_on', 'note'}, 'source card')
    for field in ('id', 'location', 'note'):
        _text(card[field], f'source.{field}')
    if not isinstance(card['kind'], str) or card['kind'] not in SOURCE_KINDS:
        raise ValueError('invalid source.kind')
    _commit(card['revision'], 'source.revision', nullable=True)
    if _day(card['audited_on'], 'source.audited_on') > updated:
        raise ValueError('source audit is later than index updated_on')
    location = card['location']
    if card['kind'] == 'local_record' or (
        card['kind'] == 'target_evidence' and not location.startswith('https://')
    ):
        # These are inert repository-relative locators, never files to open.
        path = PurePosixPath(location)
        if (path.is_absolute() or '\\' in location or ':' in location
                or any(part in ('', '.', '..') for part in location.split('/'))):
            raise ValueError('local source must be a safe repository-relative locator')
    else:
        url = urlsplit(location)
        if (url.scheme != 'https' or url.netloc != 'github.com'
                or url.username or url.password or not url.path.startswith('/')):
            raise ValueError('remote source must be an HTTPS github.com locator')
        if any(part in ('.', '..') for part in url.path.split('/')):
            raise ValueError('source URL contains traversal')


def validate_index(index):
    """Validate facts and review evidence without opening any source locator."""
    _fields(index, {'schema_version', 'description', 'updated_on', 'claim_scope', 'entries'}, 'index')
    if type(index['schema_version']) is not int or index['schema_version'] != 1:
        raise ValueError('schema_version must be integer 1')
    _text(index['description'], 'description')
    if index['claim_scope'] != CLAIM_SCOPE:
        raise ValueError('index claim_scope must preserve the historical-navigation boundary')
    updated = _day(index['updated_on'], 'updated_on')
    if not isinstance(index['entries'], list):
        raise ValueError('entries must be a list')
    ids, prs = set(), set()
    for entry in index['entries']:
        _fields(entry, {'id', 'framework', 'models', 'operators', 'keywords', 'title',
                        'summary', 'pr', 'metadata_verified', 'metadata_audited_on',
                        'review', 'applicability', 'source_cards'}, 'entry')
        for field in ('id', 'framework', 'title', 'summary'):
            _text(entry[field], field)
        for field in ('id', 'framework'):
            if not SLUG.fullmatch(entry[field]):
                raise ValueError(f'{field} must be a lowercase slug')
        if entry['id'] in ids:
            raise ValueError('duplicate entry id')
        ids.add(entry['id'])
        for field in ('models', 'operators', 'keywords'):
            _texts(entry[field], field)
        pr = entry['pr']
        _fields(pr, {'repository', 'number', 'url', 'state', 'merged', 'head_commit',
                     'merge_commit', 'created_on', 'closed_on', 'merged_on'}, 'pr')
        if not isinstance(pr['repository'], str) or not REPOSITORY.fullmatch(pr['repository']):
            raise ValueError('invalid PR repository')
        if type(pr['number']) is not int or pr['number'] < 1:
            raise ValueError('PR number must be a positive integer')
        expected_url = f'https://github.com/{pr["repository"]}/pull/{pr["number"]}'
        if pr['url'] != expected_url:
            raise ValueError('PR URL must identify the exact repository and pull request')
        if expected_url.casefold() in prs:
            raise ValueError('duplicate PR')
        prs.add(expected_url.casefold())
        if pr['state'] not in ('open', 'closed') or type(pr['merged']) is not bool:
            raise ValueError('invalid PR state/merged facts')
        _commit(pr['head_commit'], 'pr.head_commit')
        _commit(pr['merge_commit'], 'pr.merge_commit', nullable=True)
        created = _day(pr['created_on'], 'pr.created_on')
        closed = _day(pr['closed_on'], 'pr.closed_on', nullable=True)
        merged = _day(pr['merged_on'], 'pr.merged_on', nullable=True)
        if ((pr['state'] == 'closed') != (closed is not None)
                or (closed is not None and closed < created)):
            raise ValueError('PR closed date conflicts with state or creation date')
        if pr['merged']:
            if (pr['state'] != 'closed' or merged is None or pr['merge_commit'] is None
                    or merged < created or merged != closed):
                raise ValueError('merged PR requires consistent merge/close facts')
        elif merged is not None or pr['merge_commit'] is not None:
            raise ValueError('unmerged PR cannot have merge facts')
        if type(entry['metadata_verified']) is not bool:
            raise ValueError('metadata_verified must be boolean')
        audited = _day(entry['metadata_audited_on'], 'metadata_audited_on', nullable=True)
        if entry['metadata_verified'] != (audited is not None):
            raise ValueError('metadata verification requires its own audit date')
        if any(day is not None and day > updated for day in (created, closed, merged, audited)):
            raise ValueError('PR dates exceed index updated_on')
        if audited and (audited < created or (closed and audited < closed)):
            raise ValueError('metadata audit predates observed PR facts')
        cards = entry['source_cards']
        if not isinstance(cards, list) or not cards:
            raise ValueError('source_cards must be nonempty')
        source_ids = {}
        for card in cards:
            _source(card, updated)
            if card['id'] in source_ids:
                raise ValueError('duplicate source card id')
            source_ids[card['id']] = card
        if entry['metadata_verified'] and not any(
            card['kind'] == 'upstream_metadata' and card['location'] == expected_url
            and card['revision'] == pr['head_commit']
            and card['audited_on'] == entry['metadata_audited_on'] for card in cards
        ):
            raise ValueError('verified metadata requires a source card bound to the PR head and audit date')
        review = entry['review']
        _fields(review, {'level', 'diff_reviewed_on', 'diff_evidence', 'target_reproduced_on',
                         'target_scope', 'target_evidence'}, 'review')
        if review['level'] not in REVIEW_LEVELS:
            raise ValueError('invalid review level')
        diff_day = _day(review['diff_reviewed_on'], 'diff_reviewed_on', nullable=True)
        target_day = _day(review['target_reproduced_on'], 'target_reproduced_on', nullable=True)
        for field, kind in (('diff_evidence', 'upstream_diff'), ('target_evidence', 'target_evidence')):
            _texts(review[field], field, empty=True)
            if any(source_ids.get(key, {}).get('kind') != kind for key in review[field]):
                raise ValueError(f'{field} must reference source cards of kind {kind}')
        if review['level'] == 'discovery':
            if (diff_day or target_day or review['diff_evidence'] or review['target_evidence']
                    or review['target_scope'] is not None):
                raise ValueError('discovery cannot carry diff-review or reproduction claims')
        else:
            if not diff_day or not review['diff_evidence']:
                raise ValueError('diff-reviewed levels require dated diff evidence')
            if any(source_ids[key]['revision'] != pr['head_commit']
                   or source_ids[key]['audited_on'] != review['diff_reviewed_on']
                   for key in review['diff_evidence']):
                raise ValueError('diff evidence must bind the indexed PR head and review date')
            if review['level'] == 'target_reproduced':
                _text(review['target_scope'], 'target_scope')
                if not target_day or not review['target_evidence'] or target_day < diff_day:
                    raise ValueError('target reproduction requires dated, scoped target evidence')
                if any(source_ids[key]['revision'] not in (pr['head_commit'], pr['merge_commit'])
                       or source_ids[key]['audited_on'] != review['target_reproduced_on']
                       for key in review['target_evidence']):
                    raise ValueError('target evidence must bind the PR head/merge and reproduction date')
            elif target_day or review['target_evidence'] or review['target_scope'] is not None:
                raise ValueError('diff_reviewed cannot carry target reproduction claims')
        if any(day and not created <= day <= updated for day in (diff_day, target_day)):
            raise ValueError('review dates must lie between PR creation and index update')
        applicability = entry['applicability']
        _fields(applicability, {'conditions', 'gaps', 'current_dispatch'}, 'applicability')
        _texts(applicability['conditions'], 'conditions')
        _texts(applicability['gaps'], 'gaps')
        if applicability['current_dispatch'] != 'unknown':
            raise ValueError('an offline historical index cannot certify current dispatch')


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f'duplicate JSON key: {key}')
        value[key] = item
    return value


def _constant(value):
    raise ValueError(f'non-finite JSON value: {value}')


def load_index(path):
    """Read only the explicitly selected JSON index, never paths inside it."""
    selected = Path(path).resolve(strict=True)
    if not selected.is_file() or selected.stat().st_size > 4 * 1024 * 1024:
        raise ValueError('index must be a regular JSON file no larger than 4 MiB')
    raw = selected.read_bytes()
    index = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
    validate_index(index)
    return index, {'path': str(selected), 'sha256': hashlib.sha256(raw).hexdigest()}


def query_index(index, source, *, framework=None, model=None, operator=None,
                keywords=(), review_level=None, limit=10):
    """Deterministic AND filtering; matches are evidence navigation, not gates."""
    validate_index(index)
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError('limit must be an integer from 1 to 1000')
    if review_level is not None and review_level not in REVIEW_LEVELS:
        raise ValueError('invalid review level filter')
    for name, value in (('framework', framework), ('model', model), ('operator', operator)):
        if value is not None:
            _text(value, f'{name} filter')
    for phrase in keywords:
        _text(phrase, 'keyword filter')
    terms = list(dict.fromkeys(term.casefold() for phrase in keywords for term in phrase.split()))
    matches = []
    for entry in sorted(index['entries'], key=lambda item: item['id']):
        if framework and entry['framework'].casefold() != framework.casefold():
            continue
        if model and not any(model.casefold() in value.casefold() for value in entry['models']):
            continue
        if operator and not any(operator.casefold() in value.casefold() for value in entry['operators']):
            continue
        if review_level and entry['review']['level'] != review_level:
            continue
        searchable = [entry['id'], entry['framework'], *entry['models'], *entry['operators'],
                      *entry['keywords'], entry['title'], entry['summary'], entry['pr']['url'],
                      *entry['applicability']['conditions'], *entry['applicability']['gaps']]
        haystack = ' '.join(searchable).casefold()
        if all(term in haystack for term in terms):
            matches.append(entry)
    return {'schema_version': 1, 'status': 'matched' if matches else 'no_matches',
            'claim_scope': CLAIM_SCOPE, 'source_index': source, 'index_updated_on': index['updated_on'],
            'query': {'framework': framework, 'model': model, 'operator': operator,
                      'keywords': terms, 'review_level': review_level, 'limit': limit},
            'total_matches': len(matches), 'returned': min(limit, len(matches)),
            'truncated': len(matches) > limit, 'entries': matches[:limit]}


def format_text(result):
    lines = [f'Index: {result["source_index"]["path"]}',
             f'SHA256: {result["source_index"]["sha256"]}',
             f'Status: {result["status"]}; returned {result["returned"]}/{result["total_matches"]}',
             f'Boundary: {CLAIM_SCOPE}']
    for entry in result['entries']:
        pr, review = entry['pr'], entry['review']
        lines.extend(['', f'{entry["id"]}: {entry["title"]}',
                      f'  {pr["url"]} [{pr["state"]}, merged={pr["merged"]}]',
                      f'  Framework: {entry["framework"]}; models: {", ".join(entry["models"])}',
                      f'  Operators: {", ".join(entry["operators"])}',
                      f'  Head: {pr["head_commit"]}; merge: {pr["merge_commit"]}',
                      f'  Metadata verified: {entry["metadata_verified"]} on {entry["metadata_audited_on"]}',
                      f'  Review: {review["level"]}; diff on {review["diff_reviewed_on"]}; target on {review["target_reproduced_on"]}',
                      f'  Summary: {entry["summary"]}',
                      f'  Current dispatch: {entry["applicability"]["current_dispatch"]}'])
        for condition in entry['applicability']['conditions']:
            lines.append(f'  Condition: {condition}')
        for gap in entry['applicability']['gaps']:
            lines.append(f'  Gap: {gap}')
        if review['target_scope']:
            lines.append(f'  Historical target scope: {review["target_scope"]}')
        for card in entry['source_cards']:
            lines.append(f'  Source [{card["id"]}/{card["kind"]}]: {card["location"]}; revision={card["revision"]}; audit={card["audited_on"]}; {card["note"]}')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Offline PR discovery query. Only the selected JSON index is read; sources and commands are never opened or executed.',
        epilog='Review levels: discovery = navigation only; diff_reviewed = dated diff evidence; target_reproduced = scoped historical reproduction. All leave current dispatch unknown. No matches exits 0; invalid inputs exit 2.')
    parser.add_argument('query', nargs='*', help='Whitespace-separated keywords; every term must match')
    parser.add_argument('--index', type=Path, default=DEFAULT_INDEX, help='Explicit local JSON index path')
    parser.add_argument('--framework', help='Exact case-insensitive framework/library slug')
    parser.add_argument('--model', help='Case-insensitive substring in model aliases')
    parser.add_argument('--operator', help='Case-insensitive substring in operator tags')
    parser.add_argument('--keyword', action='append', default=[], help='Additional keyword phrase; repeatable')
    parser.add_argument('--review-level', choices=REVIEW_LEVELS, help='Exact evidence level, not a minimum')
    parser.add_argument('--limit', type=int, default=10, help='Maximum returned entries, 1–1000')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args(argv)
    try:
        index, source = load_index(args.index)
        result = query_index(index, source, framework=args.framework, model=args.model,
                             operator=args.operator, keywords=args.query + args.keyword,
                             review_level=args.review_level, limit=args.limit)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        parser.error(str(error))
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(format_text(result), end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
