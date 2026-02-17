#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MongoDB Client for Streamlit Dashboard
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pymongo import MongoClient
import pandas as pd

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:ChangeMe789@mongodb:27017/')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'robust_scraper')

class DashboardMongoClient:
    """Client MongoDB optimisé pour le dashboard"""
    
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DATABASE]
        self.leaks = self.db['leaks']
        self.alerts = self.db['alerts']
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict:
        """Récupère les statistiques globales"""
        total_leaks = self.leaks.count_documents({})
        bf_leaks = self.leaks.count_documents({'is_bf_related': True})
        bert_classified = self.leaks.count_documents({'bert_prediction': {'$exists': True}})
        critical_leaks = self.leaks.count_documents({'bert_prediction.severity': 'critical'})
        
        # Recent leaks (last 24h)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_leaks = self.leaks.count_documents({'created_at': {'$gte': yesterday}})
        
        return {
            'total_leaks': total_leaks,
            'bf_leaks': bf_leaks,
            'bert_classified': bert_classified,
            'critical_leaks': critical_leaks,
            'recent_leaks': recent_leaks,
            'bf_percentage': (bf_leaks / total_leaks * 100) if total_leaks > 0 else 0
        }
    
    # ========================================================================
    # LEAKS
    # ========================================================================
    
    def get_recent_leaks(self, limit: int = 50) -> List[Dict]:
        """Récupère les leaks récents"""
        cursor = self.leaks.find().sort('created_at', -1).limit(limit)
        return list(cursor)
    
    def get_leaks_dataframe(self, filters: Dict = None, limit: int = 100) -> pd.DataFrame:
        """Récupère les leaks sous forme de DataFrame"""
        query = filters or {}
        cursor = self.leaks.find(query).sort('created_at', -1).limit(limit)
        leaks = list(cursor)
        
        if not leaks:
            return pd.DataFrame()
        
        # Flatten nested fields
        data = []
        for leak in leaks:
            row = {
                'url': leak.get('url', ''),
                'title': leak.get('title', '')[:50],
                'leak_score': leak.get('leak_score', 0),
                'ioc_count': leak.get('ioc_count', 0),
                'keyword_count': leak.get('keyword_count', 0),
                'is_bf_related': leak.get('is_bf_related', False),
                'created_at': leak.get('created_at', datetime.utcnow())
            }
            
            # BF analysis
            if leak.get('bf_analysis'):
                row['bf_score'] = leak['bf_analysis'].get('total_score', 0)
                row['bf_data_type'] = leak['bf_analysis'].get('data_type', 'unknown')
                row['bf_severity'] = leak['bf_analysis'].get('sensitivity_level', 'unknown')
            else:
                row['bf_score'] = 0
                row['bf_data_type'] = 'N/A'
                row['bf_severity'] = 'N/A'
            
            # BERT prediction
            if leak.get('bert_prediction'):
                row['bert_category'] = leak['bert_prediction'].get('category', 'unknown')
                row['bert_confidence'] = leak['bert_prediction'].get('confidence', 0)
                row['bert_severity'] = leak['bert_prediction'].get('severity', 'unknown')
            else:
                row['bert_category'] = 'N/A'
                row['bert_confidence'] = 0
                row['bert_severity'] = 'N/A'
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def get_leak_by_url_hash(self, url_hash: str) -> Optional[Dict]:
        """Récupère un leak par son url_hash"""
        return self.leaks.find_one({'url_hash': url_hash})
    
    def search_leaks(self, query: str, limit: int = 50) -> List[Dict]:
        """Recherche dans les leaks (texte)"""
        mongo_query = {
            '$or': [
                {'url': {'$regex': query, '$options': 'i'}},
                {'title': {'$regex': query, '$options': 'i'}},
                {'content': {'$regex': query, '$options': 'i'}}
            ]
        }
        cursor = self.leaks.find(mongo_query).sort('created_at', -1).limit(limit)
        return list(cursor)
    
    # ========================================================================
    # AGGREGATIONS
    # ========================================================================
    
    def get_leaks_by_category(self) -> pd.DataFrame:
        """Distribution des leaks par catégorie BERT"""
        pipeline = [
            {'$match': {'bert_prediction': {'$exists': True}}},
            {'$group': {
                '_id': '$bert_prediction.category',
                'count': {'$sum': 1},
                'avg_confidence': {'$avg': '$bert_prediction.confidence'}
            }},
            {'$sort': {'count': -1}}
        ]
        
        results = list(self.leaks.aggregate(pipeline))
        
        if not results:
            return pd.DataFrame(columns=['category', 'count', 'avg_confidence'])
        
        return pd.DataFrame([
            {
                'category': r['_id'],
                'count': r['count'],
                'avg_confidence': round(r['avg_confidence'], 3)
            }
            for r in results
        ])
    
    def get_leaks_by_severity(self) -> pd.DataFrame:
        """Distribution par sévérité BERT"""
        pipeline = [
            {'$match': {'bert_prediction.severity': {'$exists': True}}},
            {'$group': {
                '_id': '$bert_prediction.severity',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        
        results = list(self.leaks.aggregate(pipeline))
        
        if not results:
            return pd.DataFrame(columns=['severity', 'count'])
        
        return pd.DataFrame([
            {'severity': r['_id'], 'count': r['count']}
            for r in results
        ])
    
    def get_leaks_timeline(self, days: int = 7) -> pd.DataFrame:
        """Timeline des leaks (par jour)"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {'$match': {'created_at': {'$gte': start_date}}},
            {'$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$created_at'
                    }
                },
                'total': {'$sum': 1},
                'bf_related': {
                    '$sum': {'$cond': ['$is_bf_related', 1, 0]}
                },
                'critical': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$bert_prediction.severity', 'critical']},
                            1,
                            0
                        ]
                    }
                }
            }},
            {'$sort': {'_id': 1}}
        ]
        
        results = list(self.leaks.aggregate(pipeline))
        
        if not results:
            return pd.DataFrame(columns=['date', 'total', 'bf_related', 'critical'])
        
        return pd.DataFrame([
            {
                'date': r['_id'],
                'total': r['total'],
                'bf_related': r['bf_related'],
                'critical': r['critical']
            }
            for r in results
        ])
    
    # ========================================================================
    # ALERTS
    # ========================================================================
    
    def get_alerts(self, status: str = 'open', limit: int = 50) -> List[Dict]:
        """Récupère les alertes"""
        query = {'status': status} if status != 'all' else {}
        cursor = self.alerts.find(query).sort('created_at', -1).limit(limit)
        return list(cursor)
    
    def get_alerts_count(self) -> Dict:
        """Compte les alertes par statut"""
        total = self.alerts.count_documents({})
        open_alerts = self.alerts.count_documents({'status': 'open'})
        
        return {
            'total': total,
            'open': open_alerts,
            'closed': total - open_alerts
        }