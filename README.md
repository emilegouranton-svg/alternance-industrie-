# Alternance Industrie

Site statique auto-actualisé listant les offres d'alternance dans quatre
secteurs industriels : **industrie scientifique / R&D**, **maintenance
industrielle**, **méthodes / industrialisation** et **supply chain**.

Aucun serveur à maintenir, aucun coût.

## Comment ça marche

```
sectors.yaml                 → secteurs suivis, avec leurs codes ROME
scripts/fetch_offres.py      → interroge l'API et met à jour l'archive
docs/data/offres.json        → archive des offres (lue par le site)
docs/index.html/.css/.js     → le site statique
.github/workflows/update.yml → exécute le script chaque jour et publie
```

Chaque nuit, GitHub Actions :
1. Lit `sectors.yaml`
2. Interroge l'API La Bonne Alternance pour chaque secteur (regroupement de
   codes ROME)
3. Dédoublonne par identifiant d'offre
4. Met à jour `docs/data/offres.json` et pousse le commit si nécessaire

GitHub Pages redéploie automatiquement le site dans la minute qui suit.

## Installation (une seule fois)

1. **Récupérer un jeton d'accès personnel** sur
   [api.apprentissage.beta.gouv.fr](https://api.apprentissage.beta.gouv.fr)
   (inscription gratuite, quelques minutes). Le même compte/jeton que pour un
   autre projet basé sur cette API peut être réutilisé.

2. **Créer un dépôt GitHub** (public, gratuit) et y pousser le contenu de ce
   dossier :
   ```bash
   cd alternance-industrie
   git init
   git add .
   git commit -m "Initial setup"
   git branch -M main
   git remote add origin https://github.com/<votre-compte>/alternance-industrie.git
   git push -u origin main
   ```

3. **Ajouter le jeton en secret** (jamais en clair dans le code) :
   - Repo → **Settings → Secrets and variables → Actions → New repository secret**
   - Nom : `LBA_API_TOKEN`
   - Valeur : votre jeton

4. **Activer GitHub Pages**
   - **Settings → Pages**
   - Source : *Deploy from a branch*, branche `main`, dossier `/docs`

5. **Lancer la première synchronisation**
   - Onglet **Actions** → sélectionner le workflow *Mise à jour quotidienne
     des offres* → **Run workflow**

Le site sera disponible à `https://<votre-compte>.github.io/alternance-industrie/`.

## Secteurs suivis et codes ROME

| Secteur | Codes ROME | Niveaux de diplôme visés |
|---|---|---|
| Industrie scientifique / R&D | H1503, H1206 | Bac+2 à Bac+5 |
| Maintenance industrielle | I1310, I1304, I1309 | CAP à Bac+2 |
| Méthodes / Industrialisation | H1404, H1402 | Bac à Bac+5 |
| Supply Chain | N1303, N1301 | Bac à Bac+5 |

## Ajuster les secteurs suivis

Tout se passe dans `sectors.yaml` : ajouter/retirer un code ROME, changer le
niveau de diplôme visé, ou ajouter un secteur entièrement nouveau. Pas besoin
de toucher au script.

## Limite connue

L'usage de l'API La Bonne Alternance est gratuit mais réservé à un usage non
commercial (revente ou facturation d'accès à des tiers interdite) — ce qui
correspond exactement à l'usage prévu ici.
