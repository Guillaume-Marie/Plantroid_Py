# Plantroid_Py
Plant life cycle model for education
## 1. Aperçu général du modèle

**Plantroid** est un modèle de croissance de plante piloté par une boucle de simulation discrète. À chaque itération (cycle), le modèle :

1. Met à jour l’environnement (lumière, température, précipitations, CO₂, etc.).
2. Calcule les coûts et les flux des processus physiologiques (photosynthèse, transpiration, maintenance, extension, reproduction).
3. Vérifie et gère la disponibilité des ressources (sucre, eau, nutriments, réserves internes).
4. Met à jour la biomasse de la plante (répartition entre compartiments : support, photo, absorption).
5. Gère l’adaptation et la mortalité potentielle de la plante.
6. Sauvegarde les variables clés dans un historique (pour analyse et création de graphiques).

La simulation s’arrête lorsque la plante meurt ou bien quand le nombre maximal de cycles est atteint.

---

## 2. Structure et rôles des fichiers

### `time_loop.py`
- Contient la boucle principale de simulation via la fonction `run_simulation_collect_data(max_cycles)`.
- À chaque cycle :
  - Réinitialise certains champs de diagnostic.
  - Met à jour l’environnement (jour/nuit, CO₂).
  - Calcule les coûts et flux (photosynthèse, transpiration, maintenance…).
  - Décide de la réussite ou de l’échec de chaque processus.
  - Effectue les ajustements adaptatifs si nécessaire.
  - Vérifie la mortalité de la plante.
  - Enregistre les données dans l’historique.

### `global_constants.py`
- Déclare les paramètres globaux (temps maximum, pas de temps, facteurs de conversion, constantes bio-physiques comme la chaleur latente de vaporisation, etc.).
- Fournit des fonctions utilitaires (ex. `trend_is_negative()` pour détecter une tendance négative, gestion de listes, etc.).

### `Environnement_def.py`
- Décrit la structure de l’environnement (sol, litière, atmosphère).
- Définit les fonctions de mise à jour (variation journalière lumière/température, précipitations aléatoires, fluctuation du CO₂).
- La fonction `environment_hazards()` introduit des événements aléatoires (vents, insectes, champignons) qui endommagent la biomasse.

### `run_and_plot.py`
- Lance la simulation (via `run_simulation_collect_data`) et génère plusieurs graphiques :
  - Évolution de la biomasse, de la santé, des flux de ressources, de la température foliaire, etc.
- Ne contient pas de logique de modélisation, uniquement l’exécution et la visualisation.

### `Plant_def.py`
- Définit la structure (dictionnaire) de la plante :
  - Paramètres physiologiques (température optimale, vitesse de croissance maximale `r_max`, fraction de la lumière absorbée, conductance stomatique, etc.).
  - Seuils de reproduction (biomasse et santé), coûts par processus, ratios d’allocation de biomasse, réserves internes (sucre, eau, nutriments).
- Initialise l’état interne : santé, vivant/mort, biomasse totale et par compartiment, historique de stress/succès, etc.

### `history_def.py`
- Contient le dictionnaire `history` qui stocke l’évolution des variables au fil du temps (biomasse, santé, SLAI, flux, température, etc.).
- La fonction `history_update()` enregistre les données à chaque cycle pour le suivi et l’analyse.

### `functions.py`
- Représente le « cœur » des calculs physiologiques :
  - **Photosynthèse** : calcul du flux de sucre produit en fonction de la lumière, de la température, de la conductance stomatique et de la concentration en CO₂.
  - **Transpiration** : calcul du refroidissement foliaire (évaporation) et de la demande en eau, compte tenu des capacités maximales (surface foliaire, biomasse racinaire, eau disponible).
  - **Maintenance, extension et reproduction** : vérifie les ressources, calcule les coûts, consomme les flux ou les réserves, alloue la nouvelle biomasse.
  - **Stress et adaptation** : en cas d’échec (ressources insuffisantes), la santé se dégrade et on ajuste les paramètres (conductance stomatique, SLAI, allocations de biomasse…).
  - Gère la mortalité et la réserve (sucre, eau, nutriments) pour compenser les manques temporaires.

---

## 3. Principes clefs du modèle

### Compartimentation de la biomasse
- La plante est divisée en trois compartiments : 
  1. **Support** (tiges, structure),
  2. **Photo** (organes photosynthétiques),
  3. **Absorption** (racines).
- Lors de la croissance (extension), la nouvelle biomasse est répartie selon des ratios réglables, modifiables en cas de stress (réallocation pour améliorer l’accès à l’eau, optimiser la photosynthèse, etc.).

### Ressources et coûts
- Chaque processus physiologique a un coût en sucre, eau et nutriments.
- Les ressources peuvent provenir du flux instantané (photosynthèse, absorption depuis le sol) ou être piochées dans les réserves internes (jusqu’à épuisement).

### Adaptation et stress
- Le modèle suit l’historique de stress (sucre, eau, etc.).
- Selon la tendance et l’échec/réussite des processus (ex. reproduction), la plante ajuste certains paramètres (conductance stomatique, surface foliaire, réallocation de biomasse).

### Boucle environnement-plante
1. L’environnement fournit lumière, température, précipitations…
2. La plante puise des ressources selon ses capacités d’absorption et de transpiration.
3. Des chocs (vents, insectes) peuvent détruire une partie de la biomasse.
4. Si la biomasse ou la santé tombent trop bas, la plante meurt (fin de la simulation).

### Collecte de l’historique
- À chaque cycle, toutes les variables importantes (biomasse, flux, température, conductance, réserves, succès de processus, etc.) sont enregistrées dans un dictionnaire dédié.
- Cette base de données est utilisée pour l’analyse a posteriori ou pour la génération de graphiques.

---

## 4. Conclusion

Le **modèle Plantroid (v9)** est un système de simulation modulaire, codé en Python, qui itère sur :

- La dynamique des ressources (lumière, eau, nutriments, CO₂) et le bilan d’énergie.
- Les processus clés (photosynthèse, transpiration, maintenance, extension, reproduction).
- Les stratégies d’adaptation face aux stress hydriques, énergétiques ou nutritifs.
- L’allocation de biomasse dans différents organes (support, photosynthèse, racines).

Son architecture, répartie en plusieurs fichiers, facilite la compréhension et la maintenance :

- Une boucle principale dans **`time_loop.py`**.
- Des définitions pour la plante et son environnement.
- Un module central **`functions.py`** pour les calculs de physiologie et d’adaptation.
- Un système d’historique pour l’analyse dans **`history_def.py`**.
- Un module de visualisation **`run_and_plot.py`** pour tracer l’évolution temporelle des variables.

C’est ainsi un **cadre de modélisation complet** permettant de simuler et de suivre le cycle de vie d’une plante, en tenant compte de multiples facteurs biotiques et abiotiques.

---

### Pour aller plus loin
- **Exécution rapide** : 
  ```bash
  python run_and_plot.py
