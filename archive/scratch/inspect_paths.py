import json, re

files = [
 'notebooks/ds02_ensemble/01_datos_y_bases.ipynb',
 'notebooks/ds02_ensemble/02_decision_ablacion_oof_ensamble.ipynb',
 'notebooks/ds02_ensemble/03_evidencia_multisemilla_diagnostico.ipynb',
]
for f in files:
    nb=json.load(open(f,encoding='utf-8'))
    print('====',f)
    for i,c in enumerate(nb['cells']):
        if c['cell_type']!='code': continue
        src=''.join(c['source'])
        seen=set()
        for m in re.finditer(r"'[^']*'|\"[^\"]*\"", src):
            s=m.group(0)
            if ('artifacts' in s or '../' in s or 'data/' in s or 'resultados' in s or 'models/' in s or 'track_clase' in s):
                key=(i,s)
                if key not in seen:
                    seen.add(key)
                    print('  cell %d: %s' % (i,s))
