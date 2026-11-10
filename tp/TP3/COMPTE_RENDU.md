# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** G2  ·  **Membres :** Salma Chair, Hamza Zaidi, …  ·  **Date :** 10/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

Les 5 échecs viennent des deux nouveaux fichiers de tests du TP3 :

- `tests/test_client.py` : `NotImplementedError`, car le corps de `MaintaiClient.predict()` n'est pas encore écrit (c'est le sprint 2) ;
- `tests/test_ui.py` : la page, exécutée avec `AppTest`, n'affiche pas encore ce que le test attend (les indicateurs de l'onglet « Données », le résultat de l'onglet « Prédiction »), car ce sont encore des TODO.

Les 18 tests du TP2 (données, modèle, API, sécurité) passent toujours.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
File "/Users/salma/Downloads/maintai-starter-tp3/ui/app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
ModuleNotFoundError: No module named 'maintai'
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Avec `streamlit run ui/app.py`, Python ajoute à son chemin de recherche le dossier du script, c'est-à-dire `ui/`. Le package `maintai` se trouve à la racine du projet, à côté de `ui/` : Python ne le trouve donc pas. Avec `python -m streamlit ...`, Python ajoute en plus le dossier courant (la racine du projet) au chemin. `import maintai` fonctionne alors.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean() * 100:.1f} %")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)
tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True)["failure"].mean()
taux.index = taux.index.astype(str)
st.subheader(f"Taux de panne par tranche de {variable}")
st.bar_chart(taux)

st.subheader("Température / vibration")
points = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.scatter_chart(points, x="temperature_c", y="vibration_mm_s", color="panne")
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13,6 % |
| Température moyenne | … °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente nettement avec la vibration : les barres des premières tranches (vibration faible) sont basses, puis elles montent tranche après tranche, et les vibrations les plus fortes ont le taux de panne le plus élevé. La vibration est donc une des variables les plus liées à la panne, ce qui est logique physiquement : un roulement usé ou un déséquilibre fait vibrer le moteur avant qu'il casse.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

À chaque mouvement de curseur, `relance` s'affiche de nouveau dans le terminal. Streamlit réexécute **tout le script `app.py` de haut en bas** à chaque interaction de l'utilisateur. Il n'y a pas de fonctions de rappel comme en JavaScript : la page est recalculée entièrement avec les nouvelles valeurs des widgets.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Comme le script est réexécuté à chaque interaction, sans cache le fichier CSV serait relu depuis le disque à chaque mouvement de curseur. `@st.cache_data` garde en mémoire le résultat de `charger` : le premier appel lit le fichier, et les suivants (avec les mêmes arguments) renvoient directement le DataFrame déjà chargé. La page reste ainsi rapide.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
    # 1. en-tête avec la clé (seulement si une clé est donnée)
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    # 2. envoi du relevé à l'API
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    # 3. si l'API refuse (401 mauvaise clé, 422 relevé invalide...) : on lève APIError
    if r.status_code != 200:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text
        raise APIError(r.status_code, detail)
    # 4. sinon on renvoie la réponse JSON
    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 % et « ⚠️ ALERTE : risque de panne, prévoir une intervention. » |
| valeurs par défaut, fausse clé | L'API a refusé la requête : Erreur 401 : Clé API absente ou invalide |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | API injoignable : vérifiez que uvicorn est lancé et l'URL. |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une règle **du navigateur** : elle s'applique seulement quand du JavaScript dans une page web appelle une autre origine. Avec Streamlit, ce n'est pas le navigateur qui appelle l'API : c'est le serveur Streamlit, un programme Python, qui envoie la requête avec `httpx`. Comme pour `curl` ou Java, aucune vérification CORS n'a lieu. Seule la clé API compte.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, c'est **le navigateur** de l'utilisateur, avec le `fetch` en JavaScript de `index.html` (d'où la vérification CORS). Dans Streamlit, c'est **le serveur Python Streamlit**, avec `MaintaiClient` et `httpx`. Le navigateur ne parle qu'à Streamlit, jamais directement à l'API.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   `MaintaiClient` accepte un client HTTP en paramètre (`http`). Les tests lui passent un `TestClient` FastAPI, qui envoie les requêtes directement à l'application en mémoire, sans port ni serveur. Le code de `predict()` est le même ; seul le « transport » change.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une **démonstration**, je choisirais **Streamlit** : en quelques lignes de Python on a des curseurs, des indicateurs et des graphiques sur les données, sans écrire de HTML, CSS ou JavaScript. C'est idéal pour montrer rapidement le modèle.
   Pour l'**application d'un technicien**, je choisirais une **page HTML + JavaScript** (ou une vraie application front-end). Elle est légère, peut être adaptée au mobile et à l'usage terrain, et ne nécessite pas un serveur Python qui réexécute tout le script à chaque clic. On contrôle aussi entièrement l'interface. Streamlit reste plutôt un outil de prototype et d'analyse.

## 6. Le rendu Git

- Lien de la pull request : https://github.com/Hamza-AI-code/projet_developement_application_intelligente/pulls 
- Le tag `tp3` existe sur GitHub : oui (après la fusion : `git tag tp3`, `git push --tags`)
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? non

## 7. Ce qui reste flou

Le fonctionnement exact de `st.form` et de `envoye` : je comprends que le résultat disparaît après un autre clic parce que `envoye` ne vaut `True` que pendant la relance du bouton, mais je ne vois pas encore bien comment garder le résultat affiché (avec `st.session_state` ?).
