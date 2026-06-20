"""
Configuration and caching utilities for Leadership Analysis System
"""
import json
import os
from src.leadership_engine import LeadershipEngine

_engine = None
_allowed_labels = None
_label_name_map = None
_conflict_axis_map = {}
_macro_category_map = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = LeadershipEngine(data_dir='./data')
    return _engine

def get_label_config():
    global _allowed_labels, _label_name_map
    if _allowed_labels is None:
        _label_name_map = {}
        for fname in ['data/micro_labels/positive_micro_labels.json', 
                      'data/micro_labels/negative_micro_labels.json']:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for ml in data.get('micro_labels', []):
                        label_id = ml['label_id']
                        label_name = ml.get('label_name', '')
                        definition = ml.get('definition', '')
                        if definition:
                            _label_name_map[label_id] = f"{label_name}: {definition}"
                        else:
                            _label_name_map[label_id] = label_name
            except FileNotFoundError:
                pass
        
        from src.nlp_pipeline import load_allowed_labels
        with open('data/labels/positive_labels.json', 'r', encoding='utf-8') as f:
            label_schema = json.load(f)
        _allowed_labels, _ = load_allowed_labels(label_schema)
        
        try:
            with open('data/labels/negative_labels.json', 'r', encoding='utf-8') as f:
                neg_schema = json.load(f)
            neg_allowed, _ = load_allowed_labels(neg_schema)
            _allowed_labels.update(neg_allowed)
        except FileNotFoundError:
            pass
            
    return _allowed_labels, _label_name_map

def get_conflict_axis_map():
    global _conflict_axis_map
    if not _conflict_axis_map:
        _conflict_axis_map = {
            "M33-01": "integrity", "M33-03": "integrity", "M30-01": "integrity",
            "N30-01": "integrity", "N28-01": "transparency"
        }
    return _conflict_axis_map

def get_macro_category_map():
    global _macro_category_map
    if _macro_category_map is None:
        _macro_category_map = {}
        for fname in ['data/labels/positive_labels.json', 'data/labels/negative_labels.json']:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for label in data.get('labels', []):
                        category = label.get('category', '기타')
                        for micro_id in label.get('micro_labels', []):
                            _macro_category_map[micro_id] = category
            except FileNotFoundError:
                pass
    return _macro_category_map

def get_grouped_labels():
    grouped = {}
    for fname in ['data/labels/positive_labels.json', 'data/labels/negative_labels.json']:
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for label in data.get('labels', []):
                    category = label.get('category', '기타')
                    micro_ids = label.get('micro_labels', [])
                    if category not in grouped:
                        grouped[category] = []
                    grouped[category].extend(micro_ids)
        except FileNotFoundError:
            pass
    return grouped

def get_macro_category(label_id):
    return get_macro_category_map().get(label_id, "기타")

def get_trait_name_map():
    with open('data/traits/trait_definitions.json', 'r', encoding='utf-8') as f:
        return {t['trait_id']: t['trait_name'] for t in json.load(f)['traits']}

def get_trait_details(trait_id):
    if not trait_id:
        return None
    with open('data/traits/trait_definitions.json', 'r', encoding='utf-8') as f:
        for t in json.load(f)['traits']:
            if t['trait_id'] == trait_id:
                return {
                    'name': t['trait_name'],
                    'description': t.get('description', ''),
                    'strengths': t.get('strengths', []),
                    'risks': t.get('risks', [])
                }
    return None

def get_label_details(label_id):
    for fname in ['data/micro_labels/positive_micro_labels.json', 
                  'data/micro_labels/negative_micro_labels.json']:
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                for ml in json.load(f).get('micro_labels', []):
                    if ml['label_id'] == label_id:
                        return {'name': ml['label_name'], 'definition': ml.get('definition', '')}
        except FileNotFoundError:
            continue
    return {'name': 'Unknown', 'definition': ''}

def get_calibration_map():
    return {"default": 0.88}