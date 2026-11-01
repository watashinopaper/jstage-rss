"""Create one Feedly-compatible RSS feed per J-STAGE journal from official article RSS."""
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from email.utils import format_datetime

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'feeds'
OUTPUT.mkdir(exist_ok=True)
ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')


def fetch(code):
    params = urllib.parse.urlencode({'btnaction': 'JT0041', 'sryCd': code, 'rssLang': 'ja'})
    url = 'https://www.jstage.jst.go.jp/AF05S010NewRssDld?' + params
    req = urllib.request.Request(url, headers={'User-Agent': 'jstage-rss-feed/1.0 (journal update reader)'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(), url


def convert(code, name, content, source):
    root = ET.fromstring(content)
    if root.tag == 'rss':
        channel = root.find('channel')
        if channel is None or not channel.findall('item'):
            raise ValueError('RSS has no article items; refusing to replace existing feed')
        items = channel.findall('item')
    elif root.tag == '{http://www.w3.org/2005/Atom}feed':
        ns = '{http://www.w3.org/2005/Atom}'
        entries = root.findall(ns + 'entry')
        if not entries:
            raise ValueError('Atom has no article entries; refusing to replace existing feed')
        items = []
        for entry in entries:
            item = ET.Element('item')
            for field in ('title', 'summary', 'published', 'updated', 'id'):
                el = entry.find(ns + field)
                if el is not None and el.text:
                    target = {'summary':'description','published':'pubDate','updated':'pubDate','id':'guid'}.get(field,field)
                    if target == 'pubDate' and item.find('pubDate') is not None:
                        continue
                    ET.SubElement(item,target).text = el.text
            link = entry.find(ns + 'link')
            if link is not None:
                ET.SubElement(item,'link').text = link.get('href','')
            items.append(item)
    else:
        raise ValueError('Unsupported source format: ' + root.tag)
    out = ET.Element('rss', version='2.0')
    ch = ET.SubElement(out,'channel')
    for tag, value in [('title',name+' — J-STAGE 新着論文'),('link','https://www.jstage.jst.go.jp/browse/'+code),('description','J-STAGE公式論文RSSから取得した更新情報'),('language','ja'),('lastBuildDate',format_datetime(datetime.now(timezone.utc)))]:
        ET.SubElement(ch,tag).text=value
    for item in items:
        if not (item.findtext('title') and item.findtext('link')):
            raise ValueError('Article item missing title or link')
        ch.append(item)
    path=OUTPUT/(code+'.xml')
    ET.ElementTree(out).write(path,encoding='utf-8',xml_declaration=True)
    print(f'{code}: {len(items)} entries -> {path}')


def main():
    journals=json.loads((ROOT/'journals.json').read_text(encoding='utf-8'))['journals']
    if not journals:
        raise ValueError('No journals configured')
    failures=[]
    for journal in journals:
        code=journal['code']
        if not code.isascii() or not all(c.isalnum() or c in '-_' for c in code):
            failures.append(code+': invalid code');continue
        try:
            content,source=fetch(code)
            convert(code,journal['name'],content,source)
        except Exception as exc:
            failures.append(code+': '+str(exc))
    if failures:
        raise RuntimeError('; '.join(failures))

if __name__=='__main__':
    main()
