# **📝 Changelog \- Datasets Images EditSelect (v2.0)**

Cette mise à jour majeure se concentre sur l'ergonomie, la rapidité d'exécution (workflow) et la compatibilité totale avec les nouvelles versions de Gradio (v4+). L'application passe d'un outil cliquable classique à un véritable logiciel "desktop-like" ultra-réactif.

## **🚀 Nouveautés Majeures**

* **Refonte du système de Sélection (Façon Windows) :** \* La sélection d'images ne fait plus clignoter la galerie (traitement 100% JavaScript).  
  * Support du \[Ctrl \+ Clic\] pour ajouter/retirer des images individuelles.  
  * Support du \[Maj \+ Clic\] pour sélectionner une plage complète d'images d'un coup.  
  * Support du \[Ctrl \+ A\] pour tout sélectionner instantanément.  
  * **Correction :** Un clic simple affiche désormais l'image instantanément dans le visualiseur tout en réinitialisant la sélection.  
* **Menu Contextuel (Clic Droit) :** \* Ajout d'un menu volant natif sur les images de la galerie pour des actions rapides sans déplacer la souris : Sauvegarder, Ajouter aux stats, Vider la sélection.  
* **Sauvegarde Silencieuse (Auto-Save) :** \* Fini l'obligation de cliquer sur "Sauvegarder". Lors de la navigation vers une autre image (via flèches ou clic), l'outil détecte les modifications de la caption et sauvegarde le fichier automatiquement en arrière-plan (en créant un .bak de sécurité).

## **⚡ Ergonomie & Tableaux ("Excel-like")**

* **Glisser-Déposer (Drag & Drop) Indestructible :** Réécriture du système de Drag & Drop dans les tableaux de la recette pour résister aux rechargements dynamiques de Gradio 4\.  
* **Édition "Excel-like" :**  
  * Un simple clic sur une case du tableau simule un double-clic et sélectionne tout le texte instantanément. Taper un nouveau chiffre écrase l'ancien sans avoir besoin d'utiliser la touche Retour arrière.  
* **Smart Swap 2.0 (Inversion Intelligente) :** Si la priorité d'un tag est modifiée vers un numéro déjà occupé, l'ancien tag prend la place vacante automatiquement (zéro doublon). Protection ajoutée contre les index hors-limites.  
* **Panneau de Saisie Rapide :** Ajout de menus déroulants sous le tableau de recette pour changer les priorités et cibles instantanément.  
* **Boutons de déplacement :** Ajout des boutons ⬆️ Monter, ⬇️ Descendre et 🗑️ Supprimer pour réorganiser le tableau sans la souris.

## **⌨️ Raccourcis Claviers (Sécurisés)**

* **Indépendance AZERTY/QWERTY :** Les raccourcis utilisent désormais e.code pour garantir leur fonctionnement quelle que soit la langue du clavier.  
* **Nouveaux raccourcis :**  
  * \[Alt \+ Flèche Haut/Bas\] : Déplacer la ligne sélectionnée dans le tableau.  
  * \[Ctrl \+ F\] : Placer le curseur directement dans la barre de recherche.  
* **Légende dynamique :** Ajout d'un encart rappelant les raccourcis sous le visualiseur d'image, mis à jour selon la langue choisie (FR/EN).

## **🐛 Corrections de Bugs (Gradio 4+ fixes)**

* **Boucle infinie des mots-clés :** Le calcul des statistiques ne se déclenche plus à chaque lettre tapée, mais uniquement lors de la frappe d'une virgule ,, de la touche Entrée, ou en quittant la case. Fin des effacements intempestifs \!  
* **Bug de surlignage HTML ("Background") :** Correction d'une faille où les mots-clés (comme "background" ou "color") corrompaient la balise HTML \<mark\> utilisée pour le surlignage. Le moteur Regex traite désormais les mots les plus longs en premier et en une seule passe.  
* **Boutons fantômes (Gradio 4\) :** Remplacement de visible=False par du CSS display: none \!important pour les boutons de synchronisation Python/JS, car Gradio 4 détruisait complètement les éléments du DOM, rendant les scripts inopérants.  
* **Bouton de copie CivitAI :** Suppression du paramètre obsolète show\_copy\_button=True qui causait des crashs au lancement, et génération d'un tableau purement Markdown formaté.  
* **Avertissement col\_count :** Mise à jour du paramètre déprécié col\_count vers column\_count pour un terminal propre.  
* **Bug de démarrage :** Sécurisation des fonctions d'interface (MSG\[lang\].get) pour éviter les crashs KeyError: None si l'initialisation de Gradio se fait avant le chargement complet des langues.

## **🌍 Internationalisation**

* Mise à jour complète des fichiers fr.json et en.json pour intégrer les instructions liées au Drag & Drop, aux nouveaux raccourcis clavier, et à la sauvegarde automatique.