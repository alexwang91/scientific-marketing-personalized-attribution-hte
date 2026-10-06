"""Dependency-free schema subset plus cross-row business invariants."""
import datetime as dt
import json
import math
from pathlib import Path

def validate_schema(value, schema, root=None, path='$'):
    root = root or schema
    if '$ref' in schema:
        target = root
        for part in schema['$ref'][2:].split('/'):
            target = target[part]
        return validate_schema(value, target, root, path)
    types = {'object':dict, 'array':list, 'string':str, 'number':(int,float), 'integer':int, 'boolean':bool}
    kind = schema.get('type')
    if kind and (not isinstance(value, types[kind]) or kind in ('number','integer') and (isinstance(value,bool) or not math.isfinite(value))):
        raise ValueError(f'{path}: expected {kind}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{path}: invalid enum')
    if isinstance(value, dict):
        for key in schema.get('required',[]):
            if key not in value:
                raise ValueError(f'{path}: missing {key}')
        props = schema.get('properties',{})
        if schema.get('additionalProperties') is False and set(value)-set(props):
            raise ValueError(f'{path}: unknown fields {set(value)-set(props)}')
        for key, item in value.items():
            if key in props:
                validate_schema(item, props[key], root, path+'.'+key)
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0): raise ValueError(f'{path}: too few items')
        for i, item in enumerate(value):
            validate_schema(item,schema.get('items',{}),root,f'{path}[{i}]')
    if isinstance(value,str) and len(value)<schema.get('minLength',0): raise ValueError(f'{path}: empty string')
    if isinstance(value,(float,int)) and not isinstance(value,bool):
        if value<schema.get('minimum',-math.inf) or value>schema.get('maximum',math.inf): raise ValueError(f'{path}: out of range')
    for rule in schema.get('allOf',[]): validate_schema(value,rule,root,path)
    if 'not' in schema:
        try: validate_schema(value,schema['not'],root,path)
        except ValueError: pass
        else: raise ValueError(f'{path}: forbidden combination')
    if 'if' in schema:
        try: validate_schema(value,schema['if'],root,path)
        except ValueError: pass
        else: validate_schema(value,schema.get('then',{}),root,path)

def validate_input(data):
    root=Path(__file__).resolve().parent
    validate_schema(data,json.loads((root/'schemas/input.schema.json').read_text()))
    keys=set(); groups={}; row_ids=set()
    for r in data['rows']:
        key=(r['country'],r['sku'],r['channel'],r['period'])
        if key in keys: raise ValueError('duplicate country × SKU × channel × period')
        keys.add(key); row_ids.add('|'.join(key)); groups.setdefault(key[:3],[]).append(r)
        try: start=dt.date.fromisoformat(r['period'])
        except ValueError: raise ValueError('period must be ISO date')
        if start.weekday()!=0: raise ValueError('weekly period must start Monday')
        if r['returns_units']>r['sell_out_units']: raise ValueError('returns exceed sell out')
        if r['sell_out_units']>r['opening_stock_units']+r['sell_in_units']: raise ValueError('sell out exceeds stock')
        if r['closing_stock_units']!=r['opening_stock_units']+r['sell_in_units']-r['sell_out_units']:
            raise ValueError('stock reconciliation failed; returns are quarantined, never saleable')
        if r['cost_eur']>r['price_eur']: raise ValueError('negative unit gross margin')
        if r['inbound_due_days']>7 and r['inbound_units']==0: raise ValueError('inbound ETA without quantity')
        if r['discount_pct']>0.5: raise ValueError('discount exceeds prototype limit')
    for records in groups.values():
        records.sort(key=lambda r:r['period'])
        for a,b in zip(records,records[1:]):
            if (dt.date.fromisoformat(b['period'])-dt.date.fromisoformat(a['period'])).days!=7: raise ValueError('weekly history gap')
            if a['closing_stock_units']!=b['opening_stock_units']: raise ValueError('stock continuity failed')
    for country, cells in data['population_cells'].items():
        if country not in {r['country'] for r in data['rows']}: raise ValueError('population has unknown country')
        validate_schema(cells,json.loads((root/'schemas/input.schema.json').read_text())['$defs']['population'])
        if {c['hard']['scenario'] for c in cells}!={'sport','commute','gift'}: raise ValueError('all three scenarios required')
    if {r['country'] for r in data['rows']}-set(data['population_cells']): raise ValueError('missing country population')
    for e in data['experiments']:
        if e['row_id'] not in row_ids: raise ValueError('experiment references unknown row')
        for arm in ('treatment','control'):
            if e[arm+'_conversions']>e[arm+'_n']: raise ValueError('experiment conversions exceed sample')
        target=dt.date.fromisoformat(e['row_id'].split('|')[-1])
        if dt.date.fromisoformat(e['available_on'])>target: raise ValueError('future experiment leakage')
    return data
