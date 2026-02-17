#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robust-Scraper URL Manager
Utilitaire pour gérer onion_urls.txt facilement
Author: Bonjour (ANSSI Burkina Faso)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# ============================================================================
# URL MANAGER
# ============================================================================

class URLManager:
    """Gestionnaire pour onion_urls.txt"""
    
    def __init__(self, filepath: str = "onion_urls.txt"):
        self.filepath = Path(filepath)
        
        if not self.filepath.exists():
            print(f"⚠️  Fichier non trouvé: {filepath}")
            print(f"Création d'un nouveau fichier...")
            self._create_empty_file()
    
    def _create_empty_file(self):
        """Créer un fichier vide avec header"""
        header = f"""# Robust-Scraper - URLs à surveiller
# Créé le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Format: une URL .onion par ligne

"""
        self.filepath.write_text(header, encoding='utf-8')
        print(f"✅ Fichier créé: {self.filepath}")
    
    def _read_urls(self) -> Tuple[List[str], List[str]]:
        """
        Lire le fichier et séparer URLs et commentaires
        Returns: (urls, all_lines)
        """
        with open(self.filepath, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        urls = [
            line.strip() 
            for line in all_lines 
            if line.strip() and not line.strip().startswith('#')
        ]
        
        return urls, all_lines
    
    def list_urls(self):
        """Afficher toutes les URLs avec numéros"""
        urls, _ = self._read_urls()
        
        if not urls:
            print("❌ Aucune URL dans le fichier")
            return
        
        print(f"\n📋 Liste des URLs ({len(urls)} total):")
        print("="*80)
        
        for i, url in enumerate(urls, 1):
            # Extraire le domaine .onion
            domain = url.split('/')[2] if '/' in url else url
            print(f"{i:3}. {url}")
            print(f"     └─ Domaine: {domain}")
        
        print("="*80)
        
        # Statistiques
        stats = self.get_stats()
        print(f"\n📊 Statistiques:")
        print(f"   • URLs actives: {stats['active_urls']}")
        print(f"   • Lignes commentées: {stats['comment_lines']}")
        print(f"   • Taille du fichier: {stats['file_size']} octets")
    
    def add_url(self, url: str, comment: str = None):
        """Ajouter une URL"""
        # Validation basique
        if '.onion' not in url:
            print(f"❌ Erreur: L'URL doit contenir .onion")
            return False
        
        if not url.startswith('http://') and not url.startswith('https://'):
            print(f"❌ Erreur: L'URL doit commencer par http:// ou https://")
            return False
        
        # Vérifier si déjà présente
        urls, all_lines = self._read_urls()
        if url in urls:
            print(f"⚠️  L'URL existe déjà: {url}")
            return False
        
        # Ajouter à la fin du fichier
        with open(self.filepath, 'a', encoding='utf-8') as f:
            if comment:
                f.write(f"\n# {comment}\n")
            f.write(f"{url}\n")
        
        print(f"✅ URL ajoutée: {url}")
        return True
    
    def remove_url(self, url_or_index):
        """Supprimer une URL par URL ou par index"""
        urls, all_lines = self._read_urls()
        
        if not urls:
            print("❌ Aucune URL à supprimer")
            return False
        
        # Si c'est un nombre, c'est un index
        try:
            index = int(url_or_index) - 1  # User uses 1-based indexing
            if 0 <= index < len(urls):
                url_to_remove = urls[index]
            else:
                print(f"❌ Index invalide: {url_or_index} (max: {len(urls)})")
                return False
        except ValueError:
            # C'est une URL
            url_to_remove = url_or_index
            if url_to_remove not in urls:
                print(f"❌ URL non trouvée: {url_to_remove}")
                return False
        
        # Reconstruire le fichier sans cette URL
        new_lines = [
            line for line in all_lines 
            if line.strip() != url_to_remove
        ]
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"✅ URL supprimée: {url_to_remove}")
        return True
    
    def validate(self):
        """Valider toutes les URLs"""
        urls, _ = self._read_urls()
        
        if not urls:
            print("❌ Aucune URL à valider")
            return
        
        print(f"\n🔍 Validation de {len(urls)} URLs...")
        print("="*80)
        
        valid_count = 0
        invalid_count = 0
        
        for i, url in enumerate(urls, 1):
            issues = []
            
            # Check .onion
            if '.onion' not in url:
                issues.append("pas de domaine .onion")
            
            # Check protocol
            if not url.startswith('http://') and not url.startswith('https://'):
                issues.append("pas de http:// ou https://")
            
            # Check length (onion v3 = 56 chars)
            domain_part = url.split('/')[2] if '/' in url else url
            if '.onion' in domain_part:
                onion_domain = domain_part.replace('.onion', '')
                if len(onion_domain) not in [16, 56]:  # v2 or v3
                    issues.append(f"longueur domaine suspecte ({len(onion_domain)} chars)")
            
            if issues:
                invalid_count += 1
                print(f"❌ {i}. {url}")
                for issue in issues:
                    print(f"   └─ ⚠️  {issue}")
            else:
                valid_count += 1
                print(f"✅ {i}. {url}")
        
        print("="*80)
        print(f"\n📊 Résultats: {valid_count} valides, {invalid_count} invalides")
    
    def get_stats(self):
        """Obtenir les statistiques du fichier"""
        urls, all_lines = self._read_urls()
        
        comment_lines = sum(
            1 for line in all_lines 
            if line.strip().startswith('#')
        )
        
        empty_lines = sum(
            1 for line in all_lines 
            if not line.strip()
        )
        
        return {
            'active_urls': len(urls),
            'total_lines': len(all_lines),
            'comment_lines': comment_lines,
            'empty_lines': empty_lines,
            'file_size': self.filepath.stat().st_size
        }
    
    def search(self, keyword: str):
        """Rechercher des URLs contenant un mot-clé"""
        urls, _ = self._read_urls()
        
        matches = [
            (i+1, url) 
            for i, url in enumerate(urls) 
            if keyword.lower() in url.lower()
        ]
        
        if not matches:
            print(f"❌ Aucune URL contenant '{keyword}'")
            return
        
        print(f"\n🔍 {len(matches)} résultat(s) pour '{keyword}':")
        print("="*80)
        
        for index, url in matches:
            print(f"{index:3}. {url}")
        
        print("="*80)

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='🕷️  Robust-Scraper URL Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python url_manager.py list
  python url_manager.py add "http://example123456.onion" -c "Forum hackers"
  python url_manager.py remove 5
  python url_manager.py remove "http://example123456.onion"
  python url_manager.py validate
  python url_manager.py search "market"
        """
    )
    
    parser.add_argument(
        'action',
        choices=['list', 'add', 'remove', 'validate', 'search', 'stats'],
        help='Action à effectuer'
    )
    
    parser.add_argument(
        'value',
        nargs='?',
        help='URL ou index (pour add/remove/search)'
    )
    
    parser.add_argument(
        '-c', '--comment',
        help='Commentaire pour la nouvelle URL (avec add)'
    )
    
    parser.add_argument(
        '-f', '--file',
        default='onion_urls.txt',
        help='Chemin vers le fichier (défaut: onion_urls.txt)'
    )
    
    args = parser.parse_args()
    
    # Initialiser le manager
    manager = URLManager(args.file)
    
    # Exécuter l'action
    if args.action == 'list':
        manager.list_urls()
    
    elif args.action == 'add':
        if not args.value:
            print("❌ Erreur: URL requise")
            print("Usage: python url_manager.py add <URL> [-c COMMENT]")
            sys.exit(1)
        manager.add_url(args.value, args.comment)
    
    elif args.action == 'remove':
        if not args.value:
            print("❌ Erreur: URL ou index requis")
            print("Usage: python url_manager.py remove <URL|INDEX>")
            sys.exit(1)
        manager.remove_url(args.value)
    
    elif args.action == 'validate':
        manager.validate()
    
    elif args.action == 'search':
        if not args.value:
            print("❌ Erreur: mot-clé requis")
            print("Usage: python url_manager.py search <KEYWORD>")
            sys.exit(1)
        manager.search(args.value)
    
    elif args.action == 'stats':
        stats = manager.get_stats()
        print("\n📊 Statistiques du fichier:")
        print("="*50)
        for key, value in stats.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        print("="*50)

if __name__ == "__main__":
    main()