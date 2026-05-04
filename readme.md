📊 Datasets Images EditSelect
Un gestionnaire et équilibreur de datasets avancé pour la préparation d'entraînements de modèles IA (Flux, Qwen, SDXL, LoRA). Conçu avec Gradio, cet outil permet de visualiser, nettoyer, analyser et extraire des sous-datasets parfaits grâce à un système de ciblage par pourcentages.
🌟 Fonctionnalités Principales
🖼️ Galerie et Ergonomie (Interface Avancée)
Design UI/UX optimisé : Panneau latéral redimensionnable et repliable pour maximiser l'espace de travail.
Sélection Multiple Intelligente : Mode de sélection visuel avec surbrillance dynamique des images ciblées.
Raccourcis Claviers Natifs : Navigation rapide avec les flèches (⬅️ ➡️) et ajout rapide aux statistiques avec Alt + S.
Menu Contextuel Custom : Clic droit sur l'image pour un accès rapide aux actions de sauvegarde et de navigation.
Mode Sombre Forcé : Pour le confort visuel lors de longues sessions de tri.
👁️ Visualiseur & Édition
Surlignage (Highlighting) : Les mots-clés que vous suivez (statistiques) s'illuminent en jaune dans vos captions.
Compteur de Tokens CLIP : Avertissement visuel en rouge si votre caption dépasse la limite habituelle des encodeurs textes (ex: > 225 tokens).
Auto-Backup : Création silencieuse d'un fichier .bak avant toute sauvegarde manuelle pour éviter la perte de données.
⚡ Édition en Batch (Masse)
Note : Les actions s'appliquent à tout le dataset ou uniquement à votre sélection multiple.
Gestion des Synonymes (Expert LoRA) : Remplacement intelligent de tags répétitifs par une liste de synonymes tournants pour enrichir le vocabulaire du modèle.
Chercher/Remplacer (avec Regex) : Support des expressions régulières pour un nettoyage en profondeur.
Nettoyage Automatique : Suppression des virgules multiples, espaces en trop et tags en doublons stricts.
Aperçu Avant/Après & Undo : Visualisez les 10 premiers changements dans un tableau avant de valider, avec possibilité d'annuler la dernière action de masse.
📈 Statistiques & Équilibrage
Recettes de Dataset : Définissez des "Cibles %" pour vos tags (ex: man:20, p0se-s1:50).
Visualisation Plotly : Génération de camemberts et d'histogrammes en temps réel pour analyser la répartition de vos concepts.
Éditeur de Tableau Interactif : Modifiez vos cibles ou supprimez des tags suivis directement depuis le tableau interactif.
Chasseur de Tags Orphelins : Détecte les fautes de frappe (tags n'apparaissant qu'une seule fois dans tout le dataset).
📁 Assistant d'Export Intelligent
Simulation d'Export : Prévisualisez la répartition finale, le nombre d'images et la galerie de votre futur export avant de copier le moindre fichier.
Stratégie 1 - Équilibrage Auto : L'algorithme sélectionne la combinaison d'images qui se rapproche le plus de vos cibles de pourcentages.
Stratégie 2 - Priorité : Remplit le dataset dans l'ordre de priorité de vos tags.
Stratégie 3 - Filtre Classique : Ne garde que les images contenant certains tags.
Limite d'Images : Possibilité de brider l'export à un nombre exact d'images (ex: un dataset parfait de 150 images max).
🚀 Installation & Lancement
Clonez ou téléchargez ce dépôt.
Assurez-vous d'avoir Python 3.10+ installé.
Installez les dépendances requises :
pip install gradio pandas plotly


Lancez l'outil :
python lora_manager.py


L'interface s'ouvrira automatiquement dans votre navigateur par défaut (lancé en local sur 127.0.0.1 pour des performances optimales et sans blocage réseau).
💡 Comment ça marche ? (Workflow recommandé)
Chargez votre dossier contenant vos paires image + .txt.
Allez dans Statistiques, cliquez sur "Remplir avec le Top 20" pour voir de quoi est composé votre dataset.
Dans l'onglet Assistant d'Export, ajustez vos cibles (ex: 50% de tel personnage, 20% de tel vêtement).
Naviguez dans la Galerie, utilisez l'Éditeur Batch pour corriger les erreurs.
Retournez dans l'Assistant d'Export, cliquez sur Simuler, puis Exporter vers votre dossier final prêt pour l'entraînement !
📜 Licence
Libre d'utilisation et de modification pour vos workflows d'IA.
