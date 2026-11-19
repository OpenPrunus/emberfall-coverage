# Couverture de code d'Emberfall

Site : https://openprunus.github.io/emberfall-coverage/

Ce dépôt est **publié automatiquement** par la CI des dépôts d'Emberfall (`emberfall-common`, `emberfall-server`, `emberfall-client`,
`emberfall-integration`) : à chaque poussée sur `main`, chacun mesure sa couverture avec `cargo-llvm-cov` et y dépose son rapport HTML
(chaque fichier ligne par ligne), sa pastille (`badges/<dépôt>.svg`) et son historique (`data/<dépôt>.json`), via `tools/publish.py`.
Ne pas modifier ces fichiers à la main.
