#!/usr/bin/env python
# encoding: utf-8
import alfred  # https://github.com/nikipore/alfred-python
import cPickle
import difflib
import HTMLParser
import os
import sys
import re
import subprocess as sp
import urllib2

_URL = 'http://docs.python.org'


def has_internet():
    try:
        urllib2.urlopen('http://google.com', timeout=2)
        return True
    except (urllib2.HTTPError, urllib2.URLError):
        return False


def get_index(v='2'):
    # local storage
    pkl = os.path.join(alfred.work(volatile=False), 'index%s.pkl' % v)
    # fetch if non existing locally
    fetch(pkl)
    return cPickle.load(open(pkl))


def clean_index(v='2'):
    # local storage
    pkl = os.path.join(alfred.work(volatile=False), 'index%s.pkl' % v)
    tmp = pkl + '.tmp'
    if fetch(tmp):
        os.rename(tmp, pkl)
        return True
    else:
        return False


def clean_HTML(parser, s):
    return parser.unescape(re.sub('<.*?>', '', s))


def fetch(pkl):
    if not os.path.exists(pkl):
        if has_internet():
            v = pkl.split('.pkl')[0][-1]
            data = urllib2.urlopen(_URL + '/%s/searchindex.js' % v).read()
            index = {}
            for d in re.findall('[\"\.\w]*:{[^{}]*}', data):
                tmpdict = re.sub('(?<![\"\w])([\.\w]{1,}):', r'"\1":',
                                 d.replace('""', '"all"'))
                index.update(eval('{' + tmpdict + '}'))

            for n in ['filenames', 'titles']:
                tmplist = re.search(',%s:(\[.*?\])' % n, data).group(1)
                index.update({n: eval(tmplist)})

            objtypes = index.pop('objtypes')
            objnames = index.pop('objnames')
            titles = index.pop('titles')
            fnames = index.pop('filenames')
            cPickle.dump([index, objtypes, objnames, titles, fnames],
                         open(pkl, 'wb'), protocol=-1)
            return True
        else:
            return False
    else:
        return True


def search(query, v='2', cutoff=0.7):

    index, objtypes, objnames, titles, fnames = get_index(v)

    # fetch function directly when giving package
    if '.' in query.strip('.'):
        tmpquery = query
        while '.' in tmpquery:
            tmpquery = '.'.join(tmpquery.split('.')[:-1])
            if tmpquery in index:
                # fake index
                index = {tmpquery: index[tmpquery]}
                tmpquery = query.replace(tmpquery + '.', '')
                break
    else:
        tmpquery = query

    order = []
    # list package directly
    if query.endswith('.') and query.rstrip('.') in index:
        q = query.rstrip('.')
        matches = {q: sorted(index[q].keys())}
    # search for similar entries
    else:
        matches = {}
        # match in all keys
        allkeys = [[i, j.keys()] for i, j in index.iteritems()]
        for k in allkeys:
            # only first match
            d = difflib.get_close_matches(tmpquery, k[1], 1, cutoff=cutoff)
            if d:
                matches.update({k[0]: [d[0]]})
            # + startswith list
            if '.' in query.strip():
                s = sorted([i for i in k[1]
                            if i.lower().startswith(tmpquery.lower())
                            and i not in d])
                matches.setdefault(k[0], []).extend(s)

        # order by closest global match
        order = difflib.get_close_matches(tmpquery,
                                          reduce(list.__add__,
                                                 matches.values()),
                                          100, cutoff)

    outmatch = []
    html = HTMLParser.HTMLParser()
    terms = matches.pop('terms', [''])[0]
    # global ordering, with modules and functions first
    for m1, m2 in sorted(matches.items(),
                         key=lambda m: (m[0] != 'all') + order.index(m[1][0])
                         if m[1][0] in order else 100):
        for m in m2:
            i = index[m1][m]
            tag = '%s%s' % ((m1 + '.') if m1 != 'all' else '', m)
            url = _URL + '/%s/%s.html?highlight=%s#%s' % (v, fnames[i[0]],
                                                          query, tag)
            outmatch.append([url,
                             u'%s — %s' % (tag, objnames[str(i[1])]),
                             clean_HTML(html, titles[i[0]])])

    if terms:
        m = terms
        terms = index['terms'][m]
        if not isinstance(terms, (list, tuple)):
            terms = [terms]
        outterm = []
        for t in terms:
            url = _URL + '/%s/%s.html?highlight=%s' % (v, fnames[t], m)
            outterm.append([url, clean_HTML(html, titles[t]), m])
        outmatch.extend(sorted(outterm, key=lambda x: x[1]))

    return outmatch


if __name__ == '__main__':

    args = alfred.args()
    # clean
    if len(args) == 1:
        # get python version from URL
        v = re.search('docs.python.org/(\d)/.*', args[0]).group(1)
        if clean_index(v):
            print 'Index rebuilt!'
        else:
            print 'No internet connexion found, index not rebuilt.'
    else:
        v, query = args
        results = []

        # define a function using the local pydoc
        define = os.path.exists('define.txt')
        if define:
            d = open('define.txt').read().strip()
            os.remove('define.txt')
            out = re.split('\n',
                           sp.Popen('/usr/bin/pydoc %s' % d, shell=True,
                                    stdout=sp.PIPE).stdout.read().strip())
            if re.search('^Help on[\s\-\w]* function', out[0]) is None:
                results.append(alfred.Item(attributes={'valid': False},
                               title='Not a function!', subtitle='',
                               icon='icon.png'))
                define = False
            else:
                out = out[2:]
                title = re.sub('^[\.\w]* = ', '', out.pop(0))
                if out and re.findall('(\w*\()', title)[0] in out[0]:
                    title += u' → ' + out.pop(0).strip()
                subtitle = []
                if out:
                    while not re.sub('^\s*', '', out[0]):
                        out.pop(0)
                    l = re.sub('^\s*', '', out.pop(0))
                    while l:
                        subtitle.append(l)
                        l = re.sub('^\s*', '', out.pop(0)) if out else ''

                results.append(alfred.Item(attributes={'valid': False},
                               title=title,
                               subtitle=' '.join(subtitle),
                               icon='icon.png'))
                query = d

        # search for documentation entries
        if query:
            for s in search(query, v):
                # do not define similar entries
                if define and len(results) == 2:
                    break
                autocomplete = re.sub('^[\d\.]*\s*', '', s[1].split(u'—')[0])
                # do not use UID, to avoid learning
                attr = {'arg': s[0],
                        'autocomplete': autocomplete.strip()}
                item =  alfred.Item(attributes=attr,
                                    title=s[1] if not define else 'Go to documentation',
                                    subtitle=s[2] if not define else '',
                                    icon='icon.png')
                results.append(item)

        alfred.write(alfred.xml(results))
