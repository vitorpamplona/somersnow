"""Forwarding pages for the addresses the snow guide had before it moved to /snow (Nov 2026).

The guide used to sit at the top of docs/ (vitorpamplona.com/somersnow/...). It now lives in docs/snow/, and the top of
the site is a PTAC home page (somerwalks.org). For every page of the guide that had an old address (each .html file in
docs/snow/ but its index), this writes a small page at the old address that forwards to the new one, keeping ?query and
#section. Links are relative, so they work at both addresses. Anything else at an old address (card images, data files)
is caught by docs/404.html, which forwards to /snow/ too. The old guide address itself is now the home page: its
Snow guide tile comes first, and old links with a #section or ?lang / ?live go straight on (see docs/index.html).

Run once from the repo root: python3 scripts/build_redirects.py (safe to run again; it skips pages that aren't stubs).
"""
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DOCS, SNOW = os.path.join(ROOT, 'docs'), os.path.join(ROOT, 'docs', 'snow')
MARK = '<!-- forwarding page: scripts/build_redirects.py -->'
PAGE = '''<!DOCTYPE html>
{mark}
<html lang="en"><head><meta charset="utf-8"><title>Moved: Somerville Snow Guide</title>
<meta name="robots" content="noindex"><link rel="canonical" href="https://somerwalks.org/snow/{canon}">
<script>location.replace('{target}' + location.search + location.hash);</script>
<meta http-equiv="refresh" content="0; url={target}">
</head><body><p>This page moved to <a href="{target}">somerwalks.org/snow/{canon}</a>.</p></body></html>
'''


def main():
    n = 0
    for dirpath, _, files in os.walk(SNOW):
        for name in files:
            if not name.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), SNOW).replace(os.sep, '/')
            if rel == 'index.html':
                continue                                          # the old guide address is the home page now
            old = os.path.join(DOCS, rel)
            if os.path.exists(old) and MARK not in open(old).read():
                continue                                          # a real page lives there now: leave it alone
            depth = rel.count('/')
            canon = rel[:-len('index.html')] if rel.endswith('index.html') else rel
            target = '../' * depth + 'snow/' + canon
            os.makedirs(os.path.dirname(old), exist_ok=True)
            with open(old, 'w') as f:
                f.write(PAGE.format(mark=MARK, canon=canon, target=target))
            n += 1
    print(f'wrote {n} forwarding pages in docs/ (old addresses -> docs/snow/)')


if __name__ == '__main__':
    main()
