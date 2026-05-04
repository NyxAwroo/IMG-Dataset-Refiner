# 📊 Datasets Images EditSelect

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Gradio](https://img.shields.io/badge/Gradio-Framework-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-Libre-green?style=for-the-badge)

**Un gestionnaire et équilibreur de datasets avancé pour la préparation d'entraînements de modèles IA**

[Installation](#-installation--lancement) • [Fonctionnalités](#-fonctionnalités-principales) • [Workflow](#-comment-ça-marche--workflow-recommandé)

</div>

---

## 🎯 À propos

Un gestionnaire et équilibreur de datasets avancé pour la préparation d'entraînements de modèles IA **(Flux, Qwen, SDXL, LoRA)**. Conçu avec **Gradio**, cet outil permet de **visualiser, nettoyer, analyser et exporter** vos datasets d'images avec une ergonomie exceptionnelle.

---

## 📸 Galerie & Aperçu

### 🎬 Interface Principale

![Datasets Images EditSelect - Vue Principale](https://github.com/BC8069EA84/Datasets-Images-EditSelect/raw/main/screenshots%20demo/2026-05-04%2002_23_18-Datasets%20Images%20EditSelect%20%E2%80%94%20Mozilla%20Firefox.png)

### 🖼️ Galerie Complète

<details open>
<summary><b>📺 Découvrez les autres interfaces (Cliquez pour plier/déplier)</b></summary>

#### 1️⃣ Vue Gestion des Tags et Édition
![Screenshot 1](https://github.com/BC8069EA84/Datasets-Images-EditSelect/raw/main/screenshots%20demo/2026-05-04%2002_19_52-Datasets%20Images%20EditSelect%20%E2%80%94%20Mozilla%20Firefox.png)

<sub>Interface de gestion des tags avec sélection multiple et édition batch</sub>

---

#### 2️⃣ Vue Statistiques et Analyse
![Screenshot 2](https://github.com/BC8069EA84/Datasets-Images-EditSelect/raw/main/screenshots%20demo/2026-05-04%2002_22_32-Datasets%20Images%20EditSelect%20%E2%80%94%20Mozilla%20Firefox.png)

<sub>Visualisation des statistiques avec graphiques Plotly et distribution des tags</sub>

---

#### 3️⃣ Vue Assistant d'Export
![Screenshot 3](https://github.com/BC8069EA84/Datasets-Images-EditSelect/raw/main/screenshots%20demo/2026-05-04%2002_23_01-Datasets%20Images%20EditSelect%20%E2%80%94%20Mozilla%20Firefox.png)

<sub>Assistant d'export intelligent avec simulation et stratégies d'équilibrage</sub>

---

#### 4️⃣ Vue Galerie Détaillée
![Screenshot 4](https://github.com/BC8069EA84/Datasets-Images-EditSelect/raw/main/screenshots%20demo/Firefox_Screenshot_2026-05-04T00-28-02.250Z.png)

<sub>Galerie avancée avec navigation et actions contextuelles</sub>

---

</details>

---

## 🌟 Fonctionnalités Principales

### 🖼️ Galerie et Ergonomie (Interface Avancée)

| Fonctionnalité | Description |
|---|---|
| **Design UI/UX Optimisé** | Panneau latéral redimensionnable et repliable pour maximiser l'espace de travail |
| **Sélection Multiple Intelligente** | Mode de sélection visuel avec surbrillance dynamique des images ciblées |
| **Raccourcis Claviers Natifs** | Navigation rapide avec les flèches (⬅️ ➡️) et ajout rapide aux statistiques avec Alt + S |
| **Menu Contextuel Custom** | Clic droit sur l'image pour un accès rapide aux actions de sauvegarde et de navigation |
| **Mode Sombre Forcé** | Pour le confort visuel lors de longues sessions de tri |

### 👁️ Visualiseur & Édition

| Fonctionnalité | Description |
|---|---|
| **Surlignage (Highlighting)** | Les mots-clés que vous suivez (statistiques) s'illuminent en jaune dans vos captions |
| **Compteur de Tokens CLIP** | Avertissement visuel en rouge si votre caption dépasse la limite habituelle (ex: > 225 tokens) |
| **Auto-Backup** | Création silencieuse d'un fichier `.bak` avant toute sauvegarde manuelle |

### ⚡ Édition en Batch (Masse)

> 💡 **Note** : Les actions s'appliquent à tout le dataset ou uniquement à votre sélection multiple.

- **Gestion des Synonymes (Expert LoRA)** : Remplacement intelligent de tags répétitifs par une liste de synonymes tournants
- **Chercher/Remplacer (avec Regex)** : Support des expressions régulières pour un nettoyage en profondeur
- **Nettoyage Automatique** : Suppression des virgules multiples, espaces en trop et tags en doublons
- **Aperçu Avant/Après & Undo** : Visualisez les 10 premiers changements avec possibilité d'annuler

### 📈 Statistiques & Équilibrage

- 🎯 **Recettes de Dataset** : Définissez des "Cibles %" pour vos tags (ex: `man:20%`, `pose-s1:50%`)
- 📊 **Visualisation Plotly** : Génération de camemberts et d'histogrammes en temps réel
- 🔧 **Éditeur de Tableau Interactif** : Modifiez vos cibles directement depuis le tableau
- 🔍 **Chasseur de Tags Orphelins** : Détecte les fautes de frappe

### 📁 Assistant d'Export Intelligent

Trois stratégies d'export pour tous les besoins :

| Stratégie | Description |
|---|---|
| **Équilibrage Auto** | L'algorithme sélectionne la combinaison d'images qui se rapproche le plus de vos cibles |
| **Priorité** | Remplit le dataset dans l'ordre de priorité de vos tags |
| **Filtre Classique** | Ne garde que les images contenant certains tags |

**Bonus** : Simulation d'export avec limite d'images personnalisée (ex: 150 images max)

---

## 🚀 Installation & Lancement

### Prérequis
- **Python 3.10+**
- Git

### Étapes

1. **Clonez le dépôt**
   ```bash
   git clone https://github.com/BC8069EA84/Datasets-Images-EditSelect.git
   cd Datasets-Images-EditSelect
   ```

2. **Installez les dépendances**
   ```bash
   pip install gradio pandas plotly
   ```

3. **Lancez l'outil**
   ```bash
   python lora_manager.py
   ```

4. **Accédez l'interface**
   - L'interface s'ouvrira automatiquement dans votre navigateur par défaut
   - Lancé en local sur `127.0.0.1` pour des performances optimales

---

## 💡 Comment ça marche ? (Workflow recommandé)

```
1️⃣  Chargez votre dossier
    └─ Contenant vos paires image + .txt

2️⃣  Analysez vos données
    └─ Onglet Statistiques → "Remplir avec le Top 20"

3️⃣  Définissez vos cibles
    └─ Assistant d'Export → Ajustez les pourcentages

4️⃣  Nettoyez & Éditez
    └─ Galerie → Utilisez l'Éditeur Batch pour corriger

5️⃣  Exportez votre dataset
    └─ Assistant d'Export → Simuler → Exporter
```

---

## 📦 Structure du Projet

```
Datasets-Images-EditSelect/
├── lora_manager.py          # Point d'entrée principal
├── readme.md                # Cette documentation
├── screenshots demo/        # Démonstration visuelle
└── requirements.txt         # Dépendances Python
```

---

## 🎓 Cas d'Usage

✅ Préparation de datasets pour **LoRA fine-tuning**  
✅ Équilibrage de datasets **multiconceptes**  
✅ Nettoyage et correction de captions en **masse**  
✅ Analyse statistique de la distribution d'un dataset  
✅ Export intelligent avec contraintes précises  

---

## 🔧 Configuration Avancée

### Variables d'Environnement
```bash
export GRADIO_SERVER_NAME=127.0.0.1
export GRADIO_SERVER_PORT=7860
```

### Personnalisation du Mode Sombre
Le mode sombre est appliqué par défaut pour un confort visuel optimal.

---

## 📄 Licence

Libre d'utilisation et de modification pour vos workflows d'IA.

---

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à :
- Signaler des bugs via les Issues
- Proposer des améliorations
- Soumettre des Pull Requests

---

<div align="center">

**Fait avec ❤️ pour la communauté IA**

[⬆️ Retour au sommet](#-datasets-images-editselect)

</div>
