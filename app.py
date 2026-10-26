import json
import random
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Plateforme Data Science & Python", layout="wide", page_icon="🎓")

BASE_DIR = Path(__file__).resolve().parent
QUIZ_SIZE = 40
LETTERS = ["A", "B", "C", "D"]

MODULES = {
    "3ème Année": ["Python & Algorithmique"],
    "4ème Année": ["Data Science (Python)", "SQL Avancé"],
}

# ======================= GENERATION DES QUESTIONS EN MEMOIRE =======================
def generate_database():
    db = []
    
    # --- 3ème Année : Python & Algorithmique ---
    for i in range(1, 161):
        db.append({
            "id": f"3A-PY-{i}", "niveau": "3ème Année", "module": "Python & Algorithmique",
            "question": f"Question Python 3A #{i} : Quel est le résultat de 9 // 2 ?",
            "code": "print(9 // 2)",
            "options": ["A. 4.5", "B. 4", "C. 5", "D. Autre"],
            "answer": "B. 4", "hint": "La division entière.",
            "explanation": "L'opérateur // renvoie la partie entière de la division."
        })

    # --- 4ème Année : Data Science ---
    for i in range(1, 161):
        db.append({
            "id": f"4A-DS-{i}", "niveau": "4ème Année", "module": "Data Science (Python)",
            "question": f"Question Data Science #{i} : Quelle méthode Pandas sélectionne des lignes selon l'étiquette (nom) ?",
            "code": "df.???(0)",
            "options": ["A. .iloc", "B. .loc", "C. .get", "D. Autre"],
            "answer": "B. .loc", "hint": "Étiquette = localisation.",
            "explanation": "La méthode .loc utilise les noms (étiquettes) pour la sélection."
        })
        
    # --- 4ème Année : SQL Avancé ---
    for i in range(1, 101):
        db.append({
            "id": f"4A-SQLA-{i}", "niveau": "4ème Année", "module": "SQL Avancé",
            "question": f"Question SQL Avancé #{i} : Quel module Python pour se connecter à MySQL ?",
            "code": "",
            "options": ["A. sqlite3", "B. mysql.connector", "C. py_sql", "D. Autre"],
            "answer": "B. mysql.connector", "hint": "Mot-clé 'connector'.",
            "explanation": "On utilise mysql.connector pour établir la connexion avec la BDD."
        })

    with open("questions.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    return db

# Chargement intelligent
with open(BASE_DIR / "questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

BY_ID = {q["id"]: q for q in QUESTIONS}

ss = st.session_state
ss.setdefault("notes", "# Mes notes de révision\n\n")
ss.setdefault("seen", {})        
ss.setdefault("mastered", set())  
ss.setdefault("quiz", None)
ss.setdefault("quiz_count", 0)

def option_list(q): return q["options"]
def correct_index(q): return q["options"].index(q["answer"])
def option_label(q, i): return q["options"][i]

def draw_ids(pool_ids, seen, nb_q_to_draw=40):
    unseen = [i for i in pool_ids if i not in seen]
    if len(unseen) >= nb_q_to_draw:
        chosen = random.sample(unseen, nb_q_to_draw)
        seen.update(chosen)
    else:
        already = [i for i in pool_ids if i in seen]
        extra = random.sample(already, min(nb_q_to_draw - len(unseen), len(already)))
        chosen = unseen + extra
        seen.clear()
        seen.update(chosen)
    random.shuffle(chosen)
    return chosen

def start_quiz(module_key, pool_ids):
    seen = ss.seen.setdefault(module_key, set())
    ss.quiz_count += 1
    nb_to_draw = min(40, len(pool_ids))
    ss.quiz = {"no": ss.quiz_count, "module": module_key, "ids": draw_ids(pool_ids, seen, nb_to_draw), "pos": 0, "answers": {}, "finished": False}

def submit_answer(qid, radio_key):
    choice = ss.get(radio_key)
    if choice is None or ss.quiz is None: return
    q = BY_ID[qid]
    ss.quiz["answers"][qid] = choice
    if choice == correct_index(q): ss.mastered.add(qid)

def go_next():
    ss.quiz["pos"] += 1
    if ss.quiz["pos"] >= len(ss.quiz["ids"]): ss.quiz["finished"] = True

def abandon_quiz(): ss.quiz = None

def render_qcm(pool, module_key):
    st.header("QCM d'entraînement")
    pool_ids = [q["id"] for q in pool]
    
    if not pool_ids:
        st.info("Les questions de ce module seront ajoutées prochainement.")
        return

    quiz = ss.quiz if (ss.quiz and ss.quiz["module"] == module_key) else None
    
    if quiz is None:
        size = min(40, len(pool_ids))
        st.write(f"Chaque QCM contient {size} questions tirées au hasard. Un nouveau QCM ne reprend pas les questions déjà tirées, tant qu'il en reste assez.")
        st.caption(f"Questions pas encore tirées : {len(pool_ids) - len(ss.seen.get(module_key, set()))} / {len(pool_ids)}")
        st.button("Démarrer un QCM", on_click=start_quiz, args=(module_key, pool_ids))
        
    elif quiz["finished"]:
        ids = quiz["ids"]
        wrong = [i for i in ids if quiz["answers"].get(i) != correct_index(BY_ID[i])]
        score = len(ids) - len(wrong)
        st.subheader("Résultat du QCM")
        st.metric("Score", f"{score} / {len(ids)}")
        
        if wrong:
            st.markdown("**Questions à revoir**")
            for i in wrong:
                q = BY_ID[i]
                with st.expander(q["question"]):
                    if q.get("code"): st.code(q["code"], language="python")
                    st.error(f"❌ Vous avez répondu : {option_label(q, quiz['answers'][i])}\n\n✅ Bonne réponse : **{q['answer']}**\n\n💡 {q['explanation']}")
        else:
            st.success("Aucune erreur sur ce QCM !")
            
        st.button("Nouveau QCM", on_click=start_quiz, args=(module_key, pool_ids))
        
    else:
        q = BY_ID[quiz["ids"][quiz["pos"]]]
        n = len(quiz["ids"])
        st.progress(quiz["pos"] / n)
        st.markdown(f"**Question {quiz['pos'] + 1} / {n}**")
        st.write(q["question"])
        if q.get("code"): st.code(q["code"], language="python")
            
        with st.expander("Indice"): st.write(q["hint"])

        key = f"radio_{quiz['no']}_{q['id']}"
        validated = q["id"] in quiz["answers"]
        
        st.radio("Votre réponse :", options=[0, 1, 2, 3], format_func=lambda i: option_label(q, i), index=None, key=key, disabled=validated)

        if not validated:
            st.button("Valider", on_click=submit_answer, args=(q["id"], key), disabled=ss.get(key) is None)
        else:
            if quiz["answers"][q["id"]] == correct_index(q):
                st.success(f"✅ Bonne réponse !\n\n{q['explanation']}")
            else:
                st.error(f"❌ Mauvaise réponse. La bonne réponse était **{q['answer']}**.\n\n{q['explanation']}")
            st.button("Voir le résultat" if quiz["pos"] == n - 1 else "Question suivante", on_click=go_next)
        
        st.divider()
        st.button("Abandonner ce QCM", on_click=abandon_quiz)


# ======================= RESUMES PEDAGOGIQUES =======================
RESUMES = {
    "1. Architecture & bases de l'algorithmique": """
### 1. Le Modèle de Von Neumann (Le Cerveau du PC)
L'ordinateur est organisé autour de 4 éléments vitaux :
- **Mémoire de masse (Disque Dur / SSD)** : Stocke les données à très long terme. (Vos films, jeux, Windows).
- **Mémoire Vive (RAM)** : Stocke temporairement les données en cours d'utilisation pour que le processeur y accède ultra-rapidement. **Elle est volatile** : pas de courant = elle se vide complètement !
- **Le CPU (Processeur)** : C'est lui qui calcule tout. Il possède une **mémoire Cache**, minuscule mais infiniment plus rapide que la RAM.
- **Les Bus de communication** (Les autoroutes de l'info) : 
   - *Bus de données* : Transporte l'information (Bidirectionnel).
   - *Bus d'adresses* : Indique au système où aller chercher l'information en mémoire (Unidirectionnel : du CPU vers la mémoire).
   - *Bus de commande* : Transmet les ordres.

### 2. Le Signal Numérique et le Binaire
- **Signal Analogique** : Une onde continue (comme le son de la voix).
- **Signal Numérique** : Des impulsions carrées. **1 = Présence de tension**, **0 = Absence de tension**.
- **Conversion Binaire** : Pour convertir `109` en binaire, on le divise par `2` jusqu'à obtenir 0. Ensuite, on lit les restes de bas en haut. `109 = 1101101`.
""",

    "2. Opérateurs, conditions, boucles": """
### 1. Opérateurs Mathématiques : Attention aux pièges !
En Python, il faut faire très attention au type de division :
- **`/` (Division réelle)** : Donne toujours un nombre à virgule (`float`). 
  *Ex: `15 / 6 = 2.5`*
- **`//` ou `DIV` (Division entière)** : Coupe la virgule et arrondit vers le **bas** (plancher). 
  *Ex: `15 // 6 = 2`. Attention aux négatifs : `-7 // 2 = -4` !*
- **`%` ou `MOD` (Modulo)** : Donne le reste de la division entière. 
  *Astuce : Si A < B, alors A % B = A. Ex: `3 % 7 = 3`.*
- **`**` (Puissance)** : Calculé de droite à gauche. 
  *Ex: `2**3**2` = `2**(3**2)` = `2**9` = 512.*

### 2. Les Conditions
Exemple de syntaxe (if / elif / else) :

    if note >= 16:
        print("Très Bien")
    elif note >= 12:
        print("Assez Bien")
    else:
        print("Ajourné")

- **Opérateurs Logiques** : `and` (les deux vrais), `or` (au moins un vrai), `not` (inverse). 
- Le **XOR** (`^`) : Vrai SI ET SEULEMENT SI les deux conditions sont différentes (Vrai XOR Faux = Vrai. Vrai XOR Vrai = Faux).

### 3. Les Boucles (Itérations)
- **`for i in range(5)`** : Boucle bornée. Compte de `0` à `4`. La fin est TOUJOURS exclue !
- **`while` (Tant que)** : Teste la condition **AVANT** d'entrer. Si c'est faux au départ, elle s'exécute 0 fois.
- **`Répéter ... Jusqu'à` (En Algo)** : Teste la condition **APRÈS**. Elle s'exécutera toujours au moins 1 fois !
""",

    "3. Listes, tuples, dictionnaires": """
### 1. La manipulation des Listes `[1, 2, 3]` (Modifiables)
- **`L.append(x)`** : Rajoute un élément à la fin. Si on ajoute une liste, ça crée une liste imbriquée.
  *Ex: `L = [1, 2]`. `L.append([3, 4])` ➔ `[1, 2, [3, 4]]` (Taille = 3).*
- **`L.extend(x)`** : Fusionne les éléments un par un à la fin.
  *Ex: `L = [1, 2]`. `L.extend([3, 4])` ➔ `[1, 2, 3, 4]` (Taille = 4).*
- **`L.insert(index, val)`** : Pousse une valeur à une place précise.
- **`L.pop(index)`** : Supprime et renvoie l'élément. Si on ne met pas d'index, ça supprime le dernier.
- **Compréhension de liste** : `[x**2 for x in range(5)]` crée directement `[0, 1, 4, 9, 16]`.

### 2. Tuples `(1, 2)` (Intouchables)
Ils sont **immuables**. Une fois créés, on ne peut plus rien changer !
*Ex: `t = (1, 2)`. Faire `t[0] = 5` génère une belle `TypeError`.*

### 3. Dictionnaires `{"clé": "valeur"}`
- Très utiles pour stocker des données sous forme de paires.
- **`d.get("age", 0)`** : Astuce de pro. Cherche la clé "age". Si elle n'existe pas, renvoie 0 (au lieu de faire planter le programme avec une `KeyError`).
- **`.keys()`** (liste des clés), **`.values()`** (liste des valeurs), **`.items()`** (liste de tuples clé-valeur).
""",

    "4. Chaînes de caractères": """
### 1. Indexation et Slicing (Découpage au scalpel)
- **Indexation** : Python compte de `0` à `n-1`. L'index `-1` désigne le TOUT dernier caractère.
- **Slicing `ch[début : fin : pas]`** : 
  - La borne de fin est TOUJOURS **exclue**.
  - `ch = "ALGORITHME"`
  - `ch[2:7]` ➔ Prend de l'index 2 ('G') jusqu'au 6 ('T'). Donne `"GORIT"`.
  - `ch[::-1]` ➔ Avec un pas négatif, ça inverse la chaîne : `"EMHTIROGLA"`.

### 2. Les Fonctions sur les textes
- **Immuabilité** : Exactement comme les tuples, une chaîne ne peut pas être modifiée. On ne peut pas faire `ch[0] = 'B'`.
- **`split()`** : Coupe une phrase en liste de mots.
- **`len(ch)`** : Donne le nombre total de caractères.
- **`replace("A", "B")`** : Remplace tous les 'A' par des 'B'.
- **F-Strings** : Permet d'insérer des variables proprement ➔ `print(f"Bonjour {nom}, tu as {note:.2f}")` (Le `:.2f` garde 2 chiffres après la virgule).
""",

    "5. Fonctions et fichiers": """
### 1. Fonctions VS Procédures
- **Fonction** : Contient le mot-clé `return`. Elle calcule quelque chose et te le renvoie pour que tu puisses le réutiliser dans une autre variable (`x = ma_fonction(5)`).
- **Procédure** : Elle fait juste une action (comme afficher un `print()`), mais elle ne te renvoie rien. En Python, si tu fais `x = ma_procedure()`, `x` vaudra `None`.

### 2. Variables Locales et Globales
- Une variable créée **dans** une fonction est "Locale". Elle n'existe pas à l'extérieur.
- Si tu veux modifier une variable "Globale" depuis l'intérieur d'une fonction, tu dois utiliser le mot magique **`global`** !

      a = 15
      def plusUn():
          global a
          a = a + 1

### 3. Gestion des Fichiers Textes
- **`'r'` (Lecture)** : Le fichier doit exister. `f.read()` lit tout. `f.readline()` lit une seule ligne.
- **`'w'` (Écriture)** : **DANGER !** Ce mode supprime tout l'ancien texte avant d'écrire le nouveau.
- **`'a'` (Append / Ajout)** : Rajoute du texte à la fin sans rien effacer.
- **L'astuce `with`** : Utiliser `with open("data.txt", "w") as f:` est génial car Python ferme automatiquement le fichier à la fin (`f.close()` est fait tout seul).
""",

    "Data Science (Python)": """
### 1. PANDAS : Le chirurgien des données
Pandas permet de manipuler d'énormes tableaux Excel via des `DataFrames`.
- **`.loc[]` (Sélection par Noms/Étiquettes)** :
  - `df.loc[1:3, "Nom":"Age"]` ➔ Attention, avec `.loc`, la borne de fin est **INCLUSE** ! Ça prendra bien la ligne 3 et la colonne "Age".
- **`.iloc[]` (Sélection par Positions Entières)** :
  - `df.iloc[1:3, 0:2]` ➔ Le "i" veut dire index. Ici, la borne de fin est **EXCLUE**.
- **Statistiques utiles** : `.mean()` (Moyenne), `.std()` (Écart-type), `.sum()` (Somme totale).

### 2. NUMPY : Calculs Scientifiques & Extremums
C'est le module de 4ème année par excellence. Les listes Numpy (`np.array`) sont beaucoup plus rapides.
- **Création** : `np.zeros((3, 4))` (Matrice 3x4 de zéros). `np.linspace(0, 10, 5)` (Génère 5 valeurs espacées également entre 0 et 10).
- **La Quête des Extremums (Maximums)** :
  - **Le Sommet Absolu** : Pour trouver LE point le plus haut de tout le graphe, on utilise `Y.max()` pour avoir sa valeur, et **`Y.argmax()`** pour avoir sa position (son indice i).
  - **Le Sommet Local (La boucle)** : Pour trouver un pic au milieu d'une courbe, il faut qu'il soit plus grand que son voisin de gauche et de droite. La condition : `if Y[i] > Y[i-1] and Y[i] > Y[i+1]:`

### 3. MATPLOTLIB : La visualisation
- **`plt.plot(X, Y, color='r', ls=':')`** : Trace une courbe (rouge, en pointillée).
- **`plt.scatter(X, Y, marker='+')`** : Disperse des points spécifiques. On l'utilise beaucoup pour marquer les extremums (les sommets) qu'on a trouvés avec Numpy.
""",

    "SQL Avancé": """
### 1. Modèle OSI et Réseaux
Pour comprendre les bases de données web, il faut comprendre le réseau :
- **Le Modèle OSI** : C'est le standard mondial en **7 couches** (1. Physique ➔ 2. Liaison ➔ 3. Réseau ➔ 4. Transport ➔ 5. Session ➔ 6. Présentation ➔ 7. Application).
- **Domaines Internet** : Le routage utilise des sous-domaines précis. Par exemple `.ac.ma` redirige vers les réseaux Académiques, et `.gov.ma` vers le Gouvernement.
- **Protocoles** : `HTTP` (pour surfer sur le web), `FTP` (File Transfer Protocol : pour uploader/télécharger des fichiers sur un serveur).

### 2. Le Langage SQL (Bases de Données Relationnelles)
- **SGBDR** : Systèmes lourds avec architecture client-serveur (MySQL, Oracle, PostgreSQL).
- **Bases Embarquées** : Bases de données sans serveur de fond, gérées dans un simple fichier (ex: SQLite).
- **Règles d'or d'écriture** : Les conventions exigent d'écrire les mots-clés SQL en **MAJUSCULES** (`CREATE`, `SELECT`, `UPDATE`) et les noms de tables en **minuscules**.

### 3. Exécuter du SQL depuis Python
C'est la compétence finale ! Comment Python parle à MySQL ?
1. **Installation** : Via le terminal `pip install mysql-connector-python`.
2. **Import** : `import mysql.connector` dans le code.
3. **Connexion** : `CNX = mysql.connector.connect(host='localhost', user='root', password='...')`
4. **Le Curseur** : C'est l'objet qui va porter vos requêtes. `CRSC = CNX.cursor()`
5. **L'exécution** : `CRSC.execute("SHOW DATABASES;")` (Affiche toutes les BDD du serveur).
"""
}

# ======================= SIDEBAR =======================
with st.sidebar:
    st.title("Espace Étudiant")
    niveau = st.selectbox("Niveau", list(MODULES.keys()))
    module = st.selectbox("Module", MODULES[niveau])
    module_key = f"{niveau}|{module}"

    pool = [q for q in QUESTIONS if q["niveau"] == niveau and q["module"] == module]
    pool_ids = {q["id"] for q in pool}

    st.divider()
    st.subheader("Score Global")
    if pool:
        done = len(pool_ids & ss.mastered)
        st.markdown(f"🏆 **{done}** questions réussies correctement.")
    else:
        st.caption("Aucune question dans ce module pour l'instant.")

    st.divider()
    st.subheader("Bloc-notes")
    st.text_area("Vos notes de révision :", key="notes", height=220)
    st.download_button(
        label="Télécharger mes notes (.md)",
        data=ss.notes,
        file_name="Mes_Notes.md",
        mime="text/markdown",
    )


# ======================= CONTENU PRINCIPAL =======================
import io
import contextlib
import types
import math
import statistics as stats_mod

st.title(f"{niveau} - {module}")

tab_resume, tab_learn, tab_qcm, tab_sql = st.tabs([
    "Résumés de cours",
    " Apprendre Python (Bases)" if niveau == "3ème Année" else " SQL dans Python & TP",
    "QCM",
    "Sandbox SQL"
])

# --- ONGLET APPRENDRE PYTHON (SEPARE ENTRE 3EME ANNEE ET 4EME ANNEE) ---
with tab_learn:
    if niveau == "3ème Année":
        st.header(" Atelier Python — 3ème Année (Bases & Algorithmique)")
        st.write("Apprenez et testez en direct les notions fondamentales du cours et des contrôles continus de **3ème Année**.")

        lecons_3a = {
            "1. Variables, print(), input() & Conversions (int, float, str)": {
                "cours": (
                    "### 1. Variables et Typage Dynamique\n"
                    "- En Python, pas besoin de déclarer le type : il est deviné automatiquement (`int`, `float`, `str`, `bool`).\n"
                    "- Le signe `=` est une **affectation** (équivalent de `<--` en algorithmique), et non une égalité mathématique.\n\n"
                    "### 2. Affichage avec `print()` et Saisie avec `input()`\n"
                    "- Par défaut, `print()` saute une ligne à la fin. L'option `end=\"\"` ou `end=\" \"` empêche le retour à la ligne.\n"
                    "- `input()` renvoie **toujours une chaîne de caractères (`str`)**. Pour calculer, il faut convertir avec `int()` ou `float()`."
                ),
                "code": (
                    "# 1. Typage automatique\n"
                    "x = 2\n"
                    "nom = 'Khadija'\n"
                    "pi = 3.14\n"
                    "print('Types :', type(x), type(nom), type(pi))\n\n"
                    "# 2. Affichage sur la même ligne avec end=''\n"
                    "print(1, end='')\n"
                    "print(2, end='')\n"
                    "print(3)\n\n"
                    "# 3. Conversion d'une entrée (simulation d'un input '4' et '12')\n"
                    "saisie = '4'\n"
                    "n = float(saisie)\n"
                    "print('Le carré de', n, 'est', n * n)\n\n"
                    "ch = '12'\n"
                    "print('Conversion int(ch) + 8 =', int(ch) + 8)"
                )
            },
            "2. Opérateurs & Traduction Algo -> Python (Exercice 1 du CC)": {
                "cours": (
                    "### 1. Correspondance Algorithmique ➔ Python\n"
                    "- **Division réelle (`/`)** : donne toujours un `float` (`9 / 2 = 4.5`).\n"
                    "- **Division entière (`DIV` ➔ `//`)** : donne le quotient entier (`15 // 6 = 2`).\n"
                    "- **Reste / Modulo (`MOD` ➔ `%`)** : donne le reste (`15 % 6 = 3`). **Règle du cours** : si `m < n`, alors `m // n = 0` et `m % n = m` (ex: `3 % 7 = 3`).\n"
                    "- **Puissance (`^` ➔ `**`)** : ex: `2 ** 3 = 8`. Écriture scientifique : `2.75e3 = 2750.0`.\n"
                    "- **Logique** : `ET` ➔ `and`, `OU` ➔ `or`, `NOT` ➔ `not`, `XOR` ➔ `^` (vrai uniquement si les 2 conditions sont différentes)."
                ),
                "code": (
                    "# Correction officielle de l'Exercice 1 du CC (Traduction Algo -> Python)\n"
                    "A = 3 % 7\n"
                    "print('Instruction 01 (A = 3 MOD 7) :', A)\n\n"
                    "B = (2 * A) % 7\n"
                    "print('Instruction 02 ((2*A) MOD 7) :', B)\n\n"
                    "C = 9 / 2 * 5 + 1\n"
                    "print('Instruction 03 (9/2*5 + 1)   :', C)\n\n"
                    "D = 'A' + ' DIV ' + 'B'\n"
                    "print('Instruction 04 (Concat)      :', D)\n\n"
                    "E = 'VRAI' + ' XOR ' + 'FAUX'\n"
                    "print('Instruction 05 (Concat)      :', E)\n\n"
                    "H = (1 == 1) ^ (1 >= 1)\n"
                    "print('Instruction 06 (XOR booléen) :', H)\n\n"
                    "L = (not H) and ((1 >= 1) or (9 > 9))\n"
                    "print('Instruction 07 (L)           :', L)\n\n"
                    "M = (not (L and L) and (H or H)) or not (L ^ H)\n"
                    "print('Instruction 08 (M)           :', M)"
                )
            },
            "3. Conditions (if/elif/else) & Boucles (Exercice 2 du CC - Tableau Data)": {
                "cours": (
                    "### 1. Tests conditionnels (`if`, `elif`, `else`)\n"
                    "- `==` (égal), `!=` (différent), `n % 5 == 0` (divisible par 5), `(n > 0) and (n < 10)` (strictement entre 0 et 10).\n"
                    "- Les deux-points `:` et l'indentation (4 espaces) sont obligatoires.\n\n"
                    "### 2. Boucles `for`, `while` et Traduction de `Répéter ... Jusqu'à`\n"
                    "- `for i in range(start, stop, step)` : la borne `stop` est toujours **exclue**.\n"
                    "- En Python, la boucle algorithmique `Répéter ... Jusqu'à (cpt >= 90 OU Data[cpt] = -100)` se traduit par une boucle avec `break`."
                ),
                "code": (
                    "# 1. Test des mentions selon la note\n"
                    "note = 13\n"
                    "if note < 10:\n"
                    "    print('Mention : Ajourné')\n"
                    "elif note < 12:\n"
                    "    print('Mention : Passable')\n"
                    "elif note < 14:\n"
                    "    print('Mention : Assez bien')\n"
                    "else:\n"
                    "    print('Mention : Bien / Très bien')\n\n"
                    "# 2. Exercice 2 du CC : Remplissage du tableau Data et recherche de Min (X) et Max (Y)\n"
                    "saisies = [15.5, 0, 8.5, 16, 10, 100, -100, 53.25, 102.3, -200.5]\n"
                    "data = []\n"
                    "cpt = 0\n"
                    "for val in saisies:\n"
                    "    cpt += 1\n"
                    "    data.append(val)\n"
                    "    if cpt >= 90 or val == -100:\n"
                    "        break\n\n"
                    "print('Instruction 11 : cpt =', cpt)\n"
                    "X = data[0]\n"
                    "Y = data[0]\n"
                    "print(f'Instruction 12 (Avant boucle) : X={X} et Y={Y}')\n\n"
                    "for k in range(1, cpt):\n"
                    "    if data[k] < X:\n"
                    "        X = data[k]\n"
                    "    if data[k] > Y:\n"
                    "        Y = data[k]\n\n"
                    "print(f'Instruction 13 (Min et Max)   : X={X} et Y={Y}')\n"
                    "print('Instruction 14 (Dernier lu)   :', data[cpt - 1])"
                )
            },
            "4. Chaînes de caractères, Indexation (+/-) & Slicing (CC ALGORITHME)": {
                "cours": (
                    "### 1. Indexation Positive et Négative\n"
                    "- Sur `CC1 = 'ALGORITHME'` (longueur 10) :\n"
                    "  - Indices positifs : `0` ('A') à `9` ('E') ➔ `CC1[2]` donne `'G'`.\n"
                    "  - Indices négatifs : `-10` ('A') à `-1` ('E') ➔ `CC1[-8]` donne aussi `'G'`.\n\n"
                    "### 2. Slicing `ch[début : fin : pas]`\n"
                    "- La borne de `fin` est **exclue**.\n"
                    "- Pour extraire `'GORIT'` : `CC1[2:7]`, `CC1[-8:-3]`, `CC1[2:-3]` ou `CC1[-8:7]`.\n"
                    "- Sur `ch1 = 'ABCD'` : 1er caractère = `ch1[0]` ou `ch1[-len(ch1)]` ou `ch1[:1]`. Dernier caractère = `ch1[-1]` ou `ch1[len(ch1)-1:len(ch1)]`."
                ),
                "code": (
                    "# 1. Slicing sur 'ALGORITHME' (Corrigé des CC)\n"
                    "CC1 = 'ALGORITHME'\n"
                    "print('CC1[2] et CC1[-8] :', CC1[2], CC1[-8])\n"
                    "print('CC1[2:7]          :', CC1[2:7])\n"
                    "print('CC1[-8:-3]        :', CC1[-8:-3])\n"
                    "print('CC1[2:-3]         :', CC1[2:-3])\n"
                    "print('CC1[-8:7]         :', CC1[-8:7])\n\n"
                    "# 2. Premier et dernier caractère de 'ABCD'\n"
                    "ch1 = 'ABCD'\n"
                    "print('1er caractère     :', ch1[0], ch1[-len(ch1)], ch1[:1])\n"
                    "print('Dernier caractère :', ch1[-1], ch1[len(ch1)-1], ch1[len(ch1)-1:len(ch1)])\n\n"
                    "# 3. Application : 2 premiers + 2 derniers caractères de 'ENCG EL JADIDA'\n"
                    "ch2 = 'ENCG EL JADIDA'\n"
                    "extrait = ch2[0:2:] + ch2[len(ch2)-2::1]\n"
                    "print('Résultat ch2      :', extrait)"
                )
            },
            "5. Listes, Tuples, Dictionnaires & Compréhensions (Exercice 3 du CC)": {
                "cours": (
                    "### 1. Méthodes sur les Listes (Modifiables)\n"
                    "- **`L.append(x)`** : ajoute `x` comme **un seul élément** à la fin (si `x` est une liste, crée une sous-liste imbriquée).\n"
                    "- **`L.extend(L2)`** : ajoute tous les éléments de `L2` **un par un**.\n"
                    "- **`L.insert(i, val)`** : insère `val` à l'indice `i`.\n"
                    "- **`L.pop(i)`** / **`del L[i]`** : supprime par indice. **`L.remove(val)`** : supprime par valeur.\n"
                    "- **`L.sort()`** (croissant), **`L.sort(reverse=True)`** (décroissant), **`L.reverse()`**.\n\n"
                    "### 2. Compréhensions, Dictionnaires, Tuples & `zip()`\n"
                    "- Liste en compréhension : `[x**2 for x in range(5)]` ou avec filtre `[x for x in range(10) if x % 2 == 0]`.\n"
                    "- Dictionnaire en compréhension : `{x: x**2 for x in range(5)}`.\n"
                    "- `zip(noms, ages)` : combine deux listes en tuples et s'arrête à la taille de la plus petite liste."
                ),
                "code": (
                    "# 1. Exercice 3 du CC (Manipulation de listes L et LL)\n"
                    "L = [-3, 10, 9, -6, 2, 3]\n"
                    "LL = [1, 2, 3]\n"
                    "print('Instruction 16 - len(L) initial :', len(L))\n\n"
                    "L.append(7)\n"
                    "L.insert(3, 3)\n"
                    "print('Instruction 17 - L[5] après insert :', L[5])\n\n"
                    "L.sort(reverse=True)\n"
                    "L.append(LL)\n"
                    "print('Instruction 18 - len(L) après append(LL) :', len(L))\n\n"
                    "L.pop(4)\n"
                    "L.extend(LL)\n"
                    "print('Instruction 19 - len(L) après pop et extend :', len(L))\n"
                    "print('Instruction 20 - (L[7])[2] :', (L[7])[2])\n\n"
                    "# 2. Compréhensions et zip()\n"
                    "pairs = {x: x**2 for x in range(10) if x % 2 == 0}\n"
                    "print('Dictionnaire pairs :', pairs)\n\n"
                    "noms = ['Mohammed', 'Safae', 'Khadija']\n"
                    "ages = [6, 13]\n"
                    "print('Résultat zip()     :', list(zip(noms, ages)))"
                )
            },
            "6. Fonctions, Portée (global) & Fichiers Textes (scores.txt)": {
                "cours": (
                    "### 1. Procédures vs Fonctions & Portée des variables\n"
                    "- Une **procédure** n'a pas de `return` (renvoie `None`). Une **vraie fonction** renvoie un résultat avec `return`.\n"
                    "- Une variable définie dans une fonction est **locale**. Pour modifier une variable globale `a` depuis une fonction, il faut écrire `global a` (sinon `UnboundLocalError`).\n\n"
                    "### 2. Manipulation de fichiers (`open`, `write`, `read`, `readline`)\n"
                    "- Modes d'ouverture : `'r'` (lecture), `'w'` (écriture, écrase le fichier), `'a'` (ajout à la fin sans écraser).\n"
                    "- `f.write(...)` n'accepte que des chaînes (`str`). `f.read(8)` lit 8 caractères. `f.readline()` lit une seule ligne."
                ),
                "code": (
                    "# 1. Fonction du CC (fct_inconnue) et portée locale\n"
                    "def fct_inconnue(E1, E2):\n"
                    "    if E1 > E2:\n"
                    "        T = E1\n"
                    "        E1 = E1 + 10\n"
                    "    else:\n"
                    "        T = E2\n"
                    "        E2 = E2 + 10\n"
                    "    print(f'Instruction 15 (interne) : E1={E1} et E2={E2}')\n"
                    "    return T\n\n"
                    "L_1, LL_1 = 9, 2\n"
                    "resultat = fct_inconnue(L_1, LL_1)\n"
                    "print(f'Instruction 21 : Résultat = {resultat}')\n"
                    "print(f'Instruction 22 : L[1]={L_1} et LL[1]={LL_1} (non modifiés)')\n\n"
                    "# 2. Mot-clé global\n"
                    "a = 15\n"
                    "def plusUn():\n"
                    "    global a\n"
                    "    a = a + 1\n"
                    "plusUn()\n"
                    "print('Après plusUn() avec global a :', a)\n\n"
                    "# 3. Écriture et lecture dans scores.txt (Exemple du cours)\n"
                    "f = open('scores.txt', 'w', encoding='utf-8')\n"
                    "f.write('Scores des joueurs :\\n')\n"
                    "f.write('Alice : ' + str(257692) + '\\n')\n"
                    "f.write('Bob : ' + str(199827) + '\\n')\n"
                    "f.close()\n\n"
                    "f = open('scores.txt', 'r', encoding='utf-8')\n"
                    "print('Lecture de 8 caractères :', repr(f.read(8)))\n"
                    "f.close()"
                )
            }
        }

        choix_3a = st.selectbox("📚 Choisissez votre leçon (Programme 3ème Année) :", list(lecons_3a.keys()))
        st.markdown(lecons_3a[choix_3a]["cours"])
        st.divider()
        st.subheader("💻 Bac à sable Python (3ème Année)")
        code_3a = st.text_area("Modifiez et testez le code Python :", value=lecons_3a[choix_3a]["code"], height=280, key=f"code_3a_{choix_3a}")

        if st.button("▶️ Exécuter le code Python"):
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code_3a, {"__builtins__": __builtins__, "math": math, "random": random, "st": stats_mod})
                sortie = buf.getvalue()
                st.success("Exécution réussie !")
                st.code(sortie if sortie else "(Aucun affichage print)", language="text")
            except Exception as err:
                st.error(f"❌ Erreur Python : {type(err).__name__} : {err}")

    else:
        st.header(" SQL dans Python (`mysql.connector`) & Data Science — 4ème Année")
        st.write("Apprenez à piloter MySQL depuis Python avec `mysql.connector` et entraînez-vous sur les TPs de Data Science de **4ème Année**.")

        lecons_4a = {
            "1. SQL dans Python : Installation & Connexion (mysql.connector)": {
                "cours": (
                    "### 1. SGBD Légers vs SGBDR Client-Serveur\n"
                    "- **Systèmes légers (`SQLite` / `MySQL Lite`)** : fichier local, sans serveur (« base embarquée »).\n"
                    "- **SGBDR professionnels (`MySQL`, `PostgreSQL`, `Oracle`, `SQL Server`)** : architecture **Client-Serveur**, gestion avancée (sécurité, concurrence, transactions).\n\n"
                    "### 2. Connecter Python à MySQL (JupyterLab / Anaconda)\n"
                    "1. **Installation obligatoire** dans Anaconda Prompt (CMD) avant d'importer :\n"
                    "   `pip install mysql-connector-python`\n"
                    "2. **Importation** : `import mysql.connector`\n"
                    "3. **Connexion au serveur** : `CNX = mysql.connector.connect(host='localhost', user='root', password='mysql2025')` (où `localhost` équivaut à `127.0.0.1`).\n"
                    "4. **Création du curseur** : `CRSC = CNX.cursor()` (l'objet qui exécute les requêtes SQL et contient les résultats)."
                ),
                "code": (
                    "import mysql.connector\n\n"
                    "# 1. Établir la connexion avec le serveur MySQL\n"
                    "CNX = mysql.connector.connect(\n"
                    "    host='localhost',      # ou '127.0.0.1'\n"
                    "    user='root',\n"
                    "    password='mysql2025'\n"
                    ")\n"
                    "print('Objet connexion :', CNX)\n\n"
                    "# 2. Créer le curseur\n"
                    "CRSC = CNX.cursor()\n"
                    "print('Curseur créé avec succès :', CRSC)"
                )
            },
            "2. SQL dans Python : SHOW, CREATE & DROP DATABASE (Code complet du cours)": {
                "cours": (
                    "### 1. Règles d'or du cours SQL & MySQL\n"
                    "- Les **commandes SQL** s'écrivent toujours en **MAJUSCULES** (`SHOW DATABASES`, `CREATE DATABASE`, `DROP DATABASE`, `USE`, `CREATE TABLE`).\n"
                    "- Les **noms de bases et de tables** s'écrivent en **minuscules** (`fincacci`, `etudiant`).\n\n"
                    "### 2. Exécuter et parcourir les résultats avec le curseur `CRSC`\n"
                    "- `CRSC.execute(\"SHOW DATABASES\")` envoie la requête au serveur.\n"
                    "- On parcourt ensuite `CRSC` avec une boucle `for db in CRSC: print(db)`."
                ),
                "code": (
                    "import mysql.connector\n\n"
                    "CNX = mysql.connector.connect(\n"
                    "    host='localhost',\n"
                    "    user='root',\n"
                    "    password='mysql2025'\n"
                    ")\n"
                    "CRSC = CNX.cursor()\n\n"
                    "print('--- 1. Bases disponibles au départ ---')\n"
                    "CRSC.execute('SHOW DATABASES')\n"
                    "for db in CRSC:\n"
                    "    print(db)\n\n"
                    "print('\\n--- 2. Création de la base S3_ENCG ---')\n"
                    "CRSC.execute('CREATE DATABASE S3_ENCG')\n"
                    "CRSC.execute('SHOW DATABASES')\n"
                    "for db in CRSC:\n"
                    "    print(db)\n\n"
                    "print('\\n--- 3. Suppression des bases S3_ENCG, fincacci et etudiant ---')\n"
                    "CRSC.execute('DROP DATABASE S3_ENCG')\n"
                    "CRSC.execute('DROP DATABASE fincacci')\n"
                    "CRSC.execute('DROP DATABASE etudiant')\n\n"
                    "CRSC.execute('SHOW DATABASES')\n"
                    "for db in CRSC:\n"
                    "    print(db)"
                )
            },
            "3. SQL dans Python : Créer une table, Insérer & Requêter (SELECT, WHERE, GROUP BY)": {
                "cours": (
                    "### Manipuler des tables relationnelles depuis Python\n"
                    "- Après `USE etudiant`, on peut exécuter `CREATE TABLE`, `INSERT INTO`, `SELECT`, `UPDATE` ou `DELETE` directement via `CRSC.execute(...)`.\n"
                    "- Rappel des clauses SQL :\n"
                    "  - `WHERE` filtre les lignes **avant** `GROUP BY`.\n"
                    "  - `HAVING` filtre les groupes **après** `GROUP BY` (ex: `HAVING COUNT(*) >= 2`).\n"
                    "  - Les dates et textes doivent être entourés d'apostrophes (ex: `'14/12/2005'`)."
                ),
                "code": (
                    "import mysql.connector\n\n"
                    "CNX = mysql.connector.connect(host='localhost', user='root', password='mysql2025')\n"
                    "CRSC = CNX.cursor()\n\n"
                    "# Création d'une table client et insertion de données\n"
                    "CRSC.execute('CREATE TABLE client (numero INT PRIMARY KEY, nom TEXT, ville TEXT)')\n"
                    "CRSC.execute(\"INSERT INTO client VALUES (1, 'Ali', 'El Jadida')\")\n"
                    "CRSC.execute(\"INSERT INTO client VALUES (2, 'Safae', 'Casablanca')\")\n"
                    "CRSC.execute(\"INSERT INTO client VALUES (3, 'Khadija', 'El Jadida')\")\n\n"
                    "print('--- Clients habitant à El Jadida (triés par nom) ---')\n"
                    "CRSC.execute(\"SELECT nom, ville FROM client WHERE ville = 'El Jadida' ORDER BY nom\")\n"
                    "for ligne in CRSC:\n"
                    "    print(ligne)\n\n"
                    "print('\\n--- Nombre de clients par ville (GROUP BY) ---')\n"
                    "CRSC.execute('SELECT ville, COUNT(*) FROM client GROUP BY ville')\n"
                    "for ligne in CRSC:\n"
                    "    print(ligne)"
                )
            },
            "4. TP1 & TP2 Data Science : Gestion des Salariés (Pandas & Statistiques par Catégorie)": {
                "cours": (
                    "### TP1 & TP2 Data Science : `BD_Salariés`\n"
                    "- Génération reproductible avec `rd.seed(10)` et création du dictionnaire `Salariés` (`Id`, `Nom Complet`, `Salaire`, `Catégorie` A/B/C).\n"
                    "- Conversion en DataFrame : `df_IS = pd.DataFrame(Salariés)`.\n"
                    "- Statistiques sur une colonne : `.min()`, `.max()`, `.mean()`, `.std()` et position des extremums avec `.argmax()` / `.argmin()`.\n"
                    "- Filtrage par catégorie : `df_SalA = df_IS[df_IS['Catégorie'] == 'A']`."
                ),
                "code": (
                    "import pandas as pd\n"
                    "import random as rd\n\n"
                    "rd.seed(10)\n"
                    "L = ['A', 'B', 'C']\n"
                    "Salariés = {\n"
                    "    'Id': [f'Ref_{i+1}' for i in range(20)],\n"
                    "    'Nom Complet': [f'NC{i+1}' for i in range(20)],\n"
                    "    'Salaire': [round(13000 + 4000 * rd.random(), 2) for i in range(20)],\n"
                    "    'Catégorie': [rd.choice(L) for i in range(20)]\n"
                    "}\n"
                    "df_IS = pd.DataFrame(Salariés)\n"
                    "print('--- Aperçu des 5 premiers salariés ---')\n"
                    "print(df_IS.head())\n\n"
                    "print('\\n--- Statistiques globales des salaires ---')\n"
                    "print('Min :', df_IS['Salaire'].min(), '| Indice argmin :', df_IS['Salaire'].argmin())\n"
                    "print('Max :', df_IS['Salaire'].max(), '| Indice argmax :', df_IS['Salaire'].argmax())\n"
                    "print('Moyenne :', round(df_IS['Salaire'].mean(), 2), '| Écart-type :', round(df_IS['Salaire'].std(), 2))\n\n"
                    "df_SalA = df_IS[df_IS['Catégorie'] == 'A']\n"
                    "print('\\n--- Salariés de la Catégorie A (Moyenne) ---')\n"
                    "print('Nombre en Catégorie A :', df_SalA.shape[0], '| Salaire Moyen A :', round(df_SalA['Salaire'].mean(), 2))"
                )
            },
            "5. TP3 & Extremums : NumPy, Fonction Lambda & Recherche d'Extremums": {
                "cours": (
                    "### Recherche d'Extremums Locaux et Absolus (TP3 & Notebook Extrem-Fct)\n"
                    "- **Attention** : `math.sin(x)` ne fonctionne que sur un seul nombre (scalaire), alors que `np.sin(X)` fonctionne sur tout un tableau NumPy.\n"
                    "- **Extremums locaux** : un point `i` est un maximum local si `Y[i] > Y[i-1] and Y[i] > Y[i+1]`.\n"
                    "- **Extremums absolus (NumPy)** : valeur `Max = Y.max()`, indice `indice_Max = Y.argmax()`, abscisse `X_max = X[indice_Max]`.\n"
                    "- **Extremums absolus (Listes)** : `L_Y = Y.tolist()`, `Max = max(L_Y)`, `indice_Max = L_Y.index(Max)`."
                ),
                "code": (
                    "import numpy as np\n\n"
                    "f = lambda x: 3 * x + 20 * np.sin(x) + 15 * np.cos(2 * x)\n"
                    "X = np.linspace(0, 20, 150)\n"
                    "Y = f(X)\n\n"
                    "# 1. Extremums absolus avec NumPy\n"
                    "Max = Y.max()\n"
                    "indice_Max = Y.argmax()\n"
                    "X_max = X[indice_Max]\n\n"
                    "Min = Y.min()\n"
                    "indice_Min = Y.argmin()\n"
                    "X_min = X[indice_Min]\n\n"
                    "print(f'Maximum absolu : Y = {Max:.2f} atteint à l_indice {indice_Max} (X = {X_max:.2f})')\n"
                    "print(f'Minimum absolu : Y = {Min:.2f} atteint à l_indice {indice_Min} (X = {X_min:.2f})')\n\n"
                    "# 2. Recherche des extremums locaux sur la grille\n"
                    "Lmax = [round(float(Y[i]), 2) for i in range(1, len(Y) - 1) if Y[i] > Y[i-1] and Y[i] > Y[i+1]]\n"
                    "print(f'Nombre de maximums locaux trouvés : {len(Lmax)} -> {Lmax}')"
                )
            },
            "6. TP4 Data Science : Analyse du DataFrame ENCGs (.loc, .iloc, Écoles, Années, Régions)": {
                "cours": (
                    "### TP4 : Étude complète des 12 ENCGs\n"
                    "- **Phase 1** : Correction des abréviations de Meknès (`ENCG-UMI`) et El Jadida (`ENCG-J`) avec `Ecoles[0:len(Ecoles)-2]` + `extend()`.\n"
                    "- **Phase 2 (Par établissement)** : Utilisation de `ENCGs.loc[i, 'Effect-1A':'Effect-5A'].sum()` (avec `.loc`, la borne `'Effect-5A'` est **incluse** !).\n"
                    "- **Phase 3 (Par année)** : Parcours de `ENCGs.columns[2:7]`.\n"
                    "- **Phase 4 (Par région)** : Création de `Region_SD` sans doublons et test `if df.shape[0] > 1:` avant de calculer l'écart-type."
                ),
                "code": (
                    "import pandas as pd\n"
                    "import random as rd\n\n"
                    "rd.seed(0)\n"
                    "Cities = ['Agadir', 'Béni Mellal', 'Casablanca', 'Dakhla', 'Fès', 'Kénitra', 'Marrakech', 'Oujda', 'Settat', 'Tanger', 'Meknès', 'El Jadida']\n"
                    "Ecoles = [f'ENCG-{ville[0]}' for ville in Cities]\n"
                    "Schools = Ecoles[0:len(Ecoles)-2]\n"
                    "Schools.extend(['ENCG-UMI', 'ENCG-J'])\n\n"
                    "L_Effectifs = [[int(150 + 100 * rd.random()) for i in range(len(Cities))] for j in range(5)]\n"
                    "D_ENCGs = {\n"
                    "    'Ecole': Schools, 'Ville': Cities,\n"
                    "    'Effect-1A': L_Effectifs[0], 'Effect-2A': L_Effectifs[1],\n"
                    "    'Effect-3A': L_Effectifs[2], 'Effect-4A': L_Effectifs[3], 'Effect-5A': L_Effectifs[4]\n"
                    "}\n"
                    "ENCGs = pd.DataFrame(D_ENCGs)\n"
                    "ENCGs['Total-Effect'] = [ENCGs.loc[i, 'Effect-1A':'Effect-5A'].sum() for i in range(ENCGs.shape[0])]\n"
                    "ENCGs['Moy-Effect'] = [ENCGs.loc[i, 'Effect-1A':'Effect-5A'].mean() for i in range(ENCGs.shape[0])]\n\n"
                    "print(ENCGs[['Ecole', 'Ville', 'Total-Effect', 'Moy-Effect']])\n"
                    "idx_max = ENCGs['Total-Effect'].argmax()\n"
                    "print(f\"\\nÉcole avec le plus grand effectif : {ENCGs['Ecole'][idx_max]} ({ENCGs['Total-Effect'].max()} étudiants)\")"
                )
            }
        }

        choix_4a = st.selectbox("📚 Choisissez votre leçon (Programme 4ème Année) :", list(lecons_4a.keys()))
        st.markdown(lecons_4a[choix_4a]["cours"])
        st.divider()
        st.subheader("💻 Simulateur Python + `mysql.connector` & Data Science (4ème Année)")
        code_4a = st.text_area("Modifiez et exécutez le code Python / SQL :", value=lecons_4a[choix_4a]["code"], height=300, key=f"code_4a_{choix_4a}")

        if st.button("▶️ Exécuter le script Python"):
            # Simulateur embarqué de mysql.connector pour exécuter le code du cours sans serveur MySQL externe
            class _SimCursor:
                def __init__(self, conn):
                    self._conn = conn
                    self._rows = []

                def execute(self, sql):
                    q = sql.strip().rstrip(";").strip()
                    qu = q.upper()
                    if qu == "SHOW DATABASES":
                        self._rows = [(d,) for d in self._conn._dbs]
                    elif qu.startswith("CREATE DATABASE "):
                        db_name = q[16:].strip().strip("`'\"").lower()
                        if db_name not in self._conn._dbs:
                            self._conn._dbs.append(db_name)
                        self._rows = []
                    elif qu.startswith("DROP DATABASE "):
                        db_name = q[14:].strip().strip("`'\"").lower()
                        if db_name in self._conn._dbs:
                            self._conn._dbs.remove(db_name)
                        self._rows = []
                    elif qu.startswith("USE "):
                        self._rows = []
                    else:
                        cur = self._conn._sqlite.cursor()
                        cur.execute(q)
                        if qu.startswith("SELECT"):
                            self._rows = cur.fetchall()
                        else:
                            self._conn._sqlite.commit()
                            self._rows = []

                def __iter__(self):
                    return iter(self._rows)

                def fetchall(self):
                    return list(self._rows)

                def __repr__(self):
                    return "MySQLCursor: (connected)"

            class _SimConnection:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs
                    self._dbs = ["information_schema", "mysql", "performance_schema", "fincacci", "etudiant"]
                    self._sqlite = sqlite3.connect(":memory:")

                def cursor(self):
                    return _SimCursor(self)

                def close(self):
                    self._sqlite.close()

                def __repr__(self):
                    return "<mysql.connector.connection_cext.CMySQLConnection object at 0x000001ENCG4A>"

            fake_mysql = types.ModuleType("mysql")
            fake_connector = types.ModuleType("mysql.connector")
            fake_connector.connect = lambda **kw: _SimConnection(**kw)
            fake_mysql.connector = fake_connector

            import sys
            import numpy as np
            sys.modules["mysql"] = fake_mysql
            sys.modules["mysql.connector"] = fake_connector

            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code_4a, {"__builtins__": __builtins__, "pd": pd, "np": np, "math": math, "random": random})
                sortie = buf.getvalue()
                st.success("Script exécuté avec succès !")
                st.code(sortie if sortie else "(Aucun affichage print)", language="text")
            except Exception as err:
                st.error(f"❌ Erreur d'exécution : {type(err).__name__} : {err}")

# --- ONGLET RESUMES ---
with tab_resume:
    if module == "Python & Algorithmique":
        chapitre = st.selectbox("Chapitre", [
            "1. Architecture & bases de l'algorithmique", 
            "2. Opérateurs, conditions, boucles",
            "3. Listes, tuples, dictionnaires",
            "4. Chaînes de caractères",
            "5. Fonctions et fichiers"
        ])
        st.markdown(RESUMES[chapitre])
    elif module == "Data Science (Python)":
        st.markdown(RESUMES["Data Science (Python)"])
    elif module == "SQL Avancé":
        st.markdown(RESUMES["SQL Avancé"])
    else:
        st.info("Le résumé de ce module n'est pas disponible dans le programme actuel.")

# --- ONGLET QCM ---
with tab_qcm:
    render_qcm(pool, module_key)

# --- ONGLET SQL (AMÉLIORÉ AVEC GUIDE ET 2 TABLES) ---
with tab_sql:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💻 Sandbox SQL")
        st.write("Testez vos requêtes sur la base de données de l'école. Vous avez accès à deux tables : `Etudiants` et `Notes`.")
        
        # Création d'une vraie petite BDD relationnelle
        conn = sqlite3.connect(":memory:")
        df_etudiants = pd.DataFrame({
            "id_etudiant": [1, 2, 3, 4, 5],
            "nom": ["Ali", "Safae", "Khadija", "Mohammed", "Youssef"],
            "filiere": ["Finance", "Audit", "Data Science", "Finance", "Audit"],
            "ville": ["El Jadida", "Casablanca", "Rabat", "El Jadida", "Marrakech"]
        })
        df_notes = pd.DataFrame({
            "id_etudiant": [1, 1, 2, 3, 3, 4, 5, 5],
            "module": ["SQL", "Python", "Compta", "Python", "Stats", "SQL", "Compta", "Audit"],
            "note": [15.5, 14.0, 16.5, 19.0, 18.0, 12.0, 14.5, 15.0]
        })
        
        df_etudiants.to_sql("Etudiants", conn, index=False, if_exists="replace")
        df_notes.to_sql("Notes", conn, index=False, if_exists="replace")

        # Zone de texte pour la requête
        query = st.text_area(
            "Écrivez votre requête SQL :",
            "SELECT filiere, COUNT(*) AS nombre_etudiants \nFROM Etudiants \nGROUP BY filiere;",
            height=150
        )
        
        if st.button("▶️ Exécuter la requête"):
            try:
                # Si c'est un SELECT, on affiche le tableau
                if query.strip().upper().startswith("SELECT"):
                    st.dataframe(pd.read_sql_query(query, conn), use_container_width=True)
                else:
                    # Pour UPDATE, INSERT, DELETE
                    cursor = conn.cursor()
                    cursor.execute(query)
                    conn.commit()
                    st.success(f"Requête exécutée avec succès ! ({cursor.rowcount} lignes modifiées)")
            except Exception as e:
                st.error(f"❌ Erreur SQL : {e}")
        conn.close()

    with col2:
        st.info("💡 **Guide SQL Rapide**")
        with st.expander("🔍 SELECT & WHERE (Filtrer)"):
            st.markdown("""
            **SELECT** choisit les colonnes, **WHERE** filtre les lignes (comme un IF).
            ```sql
            SELECT nom, ville 
            FROM Etudiants 
            WHERE ville = 'El Jadida';
            ```
            """)
            
        with st.expander("📊 GROUP BY (Regrouper)"):
            st.markdown("""
            Permet de faire des calculs par catégorie (AVG, SUM, COUNT).
            ```sql
            SELECT filiere, AVG(note) 
            FROM Etudiants 
            JOIN Notes ON Etudiants.id_etudiant = Notes.id_etudiant
            GROUP BY filiere;
            ```
            """)
            
        with st.expander("🤝 JOIN (Lier des tables)"):
            st.markdown("""
            Connecte deux tables grâce à une colonne en commun.
            ```sql
            SELECT Etudiants.nom, Notes.module, Notes.note 
            FROM Etudiants
            JOIN Notes ON Etudiants.id_etudiant = Notes.id_etudiant;
            ```
            """)
            
        with st.expander("⚖️ HAVING (Filtrer après un Group By)"):
            st.markdown("""
            WHERE filtre avant le regroupement. **HAVING** filtre le résultat du regroupement.
            ```sql
            SELECT filiere, COUNT(*) 
            FROM Etudiants 
            GROUP BY filiere 
            HAVING COUNT(*) >= 2;
            ```
            """)
            
        with st.expander("✏️ UPDATE (Modifier des données)"):
            st.markdown("""
            Modifie une ligne existante. Toujours utiliser WHERE pour ne pas tout modifier !
            ```sql
            UPDATE Notes 
            SET note = 20 
            WHERE id_etudiant = 3 AND module = 'Python';
            ```
            """)

# ======================= FOOTER =======================
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 10px; display: flex; justify-content: center; align-items: center; gap: 12px;'>
        <span>Créé par <b>ELAIDI Zakaria</b></span>
        <a href="https://www.linkedin.com/in/zakaria-elaidi/" target="_blank" style="background-color: #0A66C2; color: white; padding: 5px 14px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 14px;">
            in LinkedIn
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)