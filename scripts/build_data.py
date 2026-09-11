"""Extrai tabelas oficiais sem alterar arquivos brutos e gera dados do painel.

Uso: python scripts/build_data.py [--download]
O modo padrão usa os ZIPs versionados. --download verifica os hashes antes de
aceitar o arquivo remoto. Revisões do IBGE exigem atualização deliberada.
"""
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analysis import missing_events, relative_change

BASE = 'https://ftp.ibge.gov.br/Estatisticas_Vitais/Estimativas_sub_registro_nascimentos/'
URLS = {2022: BASE+'2022/xlsx/01nascidosvivos_xlsx_20260610.zip',
        2023: BASE+'2023/xlsx/01nascidosvivos_xlsx_20260610.zip',
        2024: BASE+'2024/xlsx/01nascidosvivos_xlsx.zip'}
UFS = dict(zip([11,12,13,14,15,16,17,21,22,23,24,25,26,27,28,29,31,32,33,35,41,42,43,50,51,52,53],
              'RO AC AM RR PA AP TO MA PI CE RN PB PE AL SE BA MG ES RJ SP PR SC RS MS MT GO DF'.split()))


def table(blob, number):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        name = next(n for n in z.namelist() if n.endswith(f'Tabela {number}.xlsx'))
        workbook = openpyxl.load_workbook(io.BytesIO(z.read(name)), data_only=True, read_only=True)
        rows = list(workbook.active.values)
        workbook.close()
        return rows


def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main():
    raw = ROOT/'data/raw'; processed = ROOT/'data/processed'
    processed.mkdir(parents=True, exist_ok=True)
    (ROOT/'dist').mkdir(exist_ok=True)
    manifest_path = ROOT/'data/sources.json'
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else []
    expected = {x['year']:x['sha256'] for x in previous}
    records, sources, blobs = [], [], {}
    for year, url in URLS.items():
        path = raw/f'01nascidosvivos_{year}.zip'
        if '--download' in sys.argv:
            data = urllib.request.urlopen(url, timeout=60).read()
            if year in expected and hashlib.sha256(data).hexdigest() != expected[year]:
                raise ValueError(f'Fonte de {year} revisada: revisar antes de substituir')
            path.write_bytes(data)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if year in expected and digest != expected[year]:
            raise ValueError(f'Arquivo local de {year} difere do manifesto')
        blobs[year] = data
        sources.append({'year':year, 'url':url, 'file':str(path.relative_to(ROOT)).replace('\\','/'),
                        'sha256':digest, 'retrieved':'2026-09-11',
                        'edition':'revisão 2026-06-10' if year<2024 else 'edição 2024'})
        region = None
        for row in table(data, '1.1')[2:]:
            code, name, total, rate, undernotification = row[:5]
            if not isinstance(total, (int,float)):
                continue
            if name == 'Total Brasil':
                level, key, name = 'country', 'BR', 'Brasil'
            elif code in UFS:
                level, key = 'state', UFS[code]
            elif name in ['Norte','Nordeste','Sudeste','Sul','Centro-Oeste']:
                level, key, region = 'region', name, name
            elif name == 'Ignorado':
                level, key = 'unknown', 'IGN'
            else:
                raise ValueError(f'Território não reconhecido: {row}')
            records.append({'year':year,'code':key,'name':name,'level':level,
                            'region':region if level=='state' else '',
                            'estimated_births':total,'rate':rate,
                            'health_underreporting':undernotification if isinstance(undernotification,(int,float)) else None,
                            'estimated_missing':round(missing_events(total,rate),6),
                            'source_table':'1.1'})
    municipalities = []
    for row in table(blobs[2024], '1.2')[2:]:
        uf, _, code, name, total, rate, health = row[:7]
        if not isinstance(code,int):
            continue
        total = total if isinstance(total,(int,float)) else None
        rate = rate if isinstance(rate,(int,float)) else None
        municipalities.append({'year':2024,'uf':UFS[uf],'code':str(code),'name':name,
                               'estimated_births':total,'rate':rate,
                               'estimated_missing':round(missing_events(total,rate),6) if total is not None and rate is not None else None,
                               'source_table':'1.2'})
    groups=[]
    for number, kind in [('1.3','maternal_age'),('1.4','birth_place')]:
        for row in table(blobs[2024],number)[2:]:
            name,total,rate,health = row[:4]
            if isinstance(total,(int,float)):
                groups.append({'kind':kind,'name':str(name),'estimated_births':total,'rate':rate,'source_table':number})
    states=[x for x in records if x['year']==2024 and x['level']=='state']
    br={x['year']:x for x in records if x['code']=='BR'}
    ranked=sorted(states,key=lambda x:x['rate'],reverse=True)
    volume=sorted(states,key=lambda x:x['estimated_missing'],reverse=True)
    summary={'br_2022':br[2022], 'br_2023':br[2023], 'br_2024':br[2024],
             'change_pp':br[2024]['rate']-br[2022]['rate'],
             'relative_change_pct':relative_change(br[2022]['rate'],br[2024]['rate']),
             'highest_rates':ranked[:5], 'highest_volumes':volume[:5],
             'top5_volume_share':sum(x['estimated_missing'] for x in volume[:5])/br[2024]['estimated_missing']*100,
             'states_above_br':sum(x['rate']>br[2024]['rate'] for x in states),
             'municipalities':len(municipalities),
             'municipalities_missing':sum(x['rate'] is None for x in municipalities)}
    write_csv(processed/'territories.csv',records)
    write_csv(processed/'municipalities_2024.csv',municipalities)
    write_csv(processed/'groups_2024.csv',groups)
    manifest_path.write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (processed/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    payload={'records':records,'groups':groups,'summary':summary,'sources':sources}
    (ROOT/'dist/data.js').write_text('window.REGISTRO_DATA = '+json.dumps(payload,ensure_ascii=False)+';\n',encoding='utf-8')
    for name in ['territories.csv','municipalities_2024.csv','groups_2024.csv']:
        (ROOT/'dist'/name).write_bytes((processed/name).read_bytes())
    print(json.dumps(summary,ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
