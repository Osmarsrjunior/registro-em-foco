import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1]/'dist'


class Links(HTMLParser):
    def __init__(self):super().__init__();self.targets=[];self.ids=set();self.lang=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html':self.lang=a.get('lang')
        if 'id' in a:self.ids.add(a['id'])
        for key in ['href','src']:
            if key in a:self.targets.append(a[key])


class SiteTests(unittest.TestCase):
    def test_local_links_and_anchors(self):
        for path in ROOT.glob('*.html'):
            parser=Links();parser.feed(path.read_text(encoding='utf-8'))
            self.assertEqual(parser.lang,'pt-BR')
            for target in parser.targets:
                u=urlsplit(target)
                if u.scheme or u.netloc:continue
                dest=path.parent/unquote(u.path) if u.path else path
                self.assertTrue(dest.is_file(),f'{path.name}: {target}')
                if u.fragment and dest.suffix=='.html':
                    other=Links();other.feed(dest.read_text(encoding='utf-8'));self.assertIn(u.fragment,other.ids)


if __name__=='__main__':unittest.main()
