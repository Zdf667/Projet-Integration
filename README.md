# Machine à cocktail

Machine à cocktail automatique pilotée par une page web en Wi-Fi. Quatre récipients contiennent chacun un liquide, une pompe péristaltique par récipient dose les ingrédients, et la machine propose uniquement les cocktails réalisables avec les ingrédients présents.

> Projet d'intégration : voir le [cahier des charges](https://github.com/Zdf667/Projet-Integration/wiki/Cahier-des-charges) pour le détail des exigences.

## Principe de fonctionnement

1. L'administrateur ouvre la page web (mode admin, protégé par un code PIN) et enregistre l'ingrédient présent dans chacun des 4 récipients.
2. La page affiche automatiquement les cocktails réalisables avec ces 4 ingrédients.
3. L'utilisateur (mode user) choisit un cocktail, confirme, puis lance la préparation depuis son téléphone.
4. La machine enchaîne les pompes selon la recette. L'avancement s'affiche sur la page web et une LED d'état indique l'état de la machine.
5. Quand le verre est prêt, la page le signale et donne un conseil de service (ex. ajouter une tranche de citron ou un glaçon).

Il n'y a **aucun écran ni commande sur la machine**, hormis la LED d'état et le bouton d'arrêt d'urgence. Un seul appareil est connecté à la fois.

## Modes

| Mode | Droits |
|---|---|
| **User** | Voir les cocktails réalisables, consulter une recette, lancer une préparation |
| **Admin** (code PIN) | Tout le mode user, plus : changer les ingrédients des récipients, lancer le nettoyage guidé |

Le nettoyage est guidé par une série d'instructions à l'écran (ex. mettre de l'eau chaude dans un grand récipient, y plonger les tuyaux, confirmer), puis les 4 lignes sont rincées.

## LED d'état

| État | LED (proposition) |
|---|---|
| Prête | Vert fixe |
| Préparation en cours | Orange clignotant |
| Verre prêt | Vert clignotant |
| Erreur | Rouge |
| Nettoyage | Bleu ou violet (à confirmer) |

## Matériel

| Élément | Quantité |
|---|---|
| Raspberry Pi Pico W (Wi-Fi, serveur web, pilotage) | 1 |
| Pompe péristaltique 12 V DC | 4 |
| Module 4 canaux MOSFET (compatible 3,3 V) + 4 diodes de roue libre | 1 |
| Alimentation 12 V, 3 à 5 A + convertisseur 12 V vers 5 V | 1 |
| Tuyau silicone alimentaire, raccords | environ 5 m |
| Récipients 0,5 à 1 L | 4 |
| LED RGB + résistances | 1 |
| Bouton d'arrêt d'urgence (contact NF) + fusible 5 A | 1 |
| Boîtier étanche pour l'électronique, bac de rétention, structure | 1 lot |
| *Bonus* : cellule de charge + module HX711 (détection du verre) | 1 |

Budget estimé : environ 135 à 250 €. La liste détaillée figure dans le cahier des charges.

## Architecture

```
  Téléphone (page web)
          │  Wi-Fi
  ┌───────▼────────┐        ┌────────────┐
  │   Pico W       │───────►│ LED d'état │
  │ serveur web +  │        └────────────┘
  │ logique        │
  └───────┬────────┘
          │ GPIO (3,3 V)
  ┌───────▼────────┐
  │ Module MOSFET  │◄── 12 V ◄── Fusible ◄── Arrêt d'urgence ◄── Alim 12 V
  │ (4 canaux)     │
  └─┬───┬───┬───┬──┘
   P1  P2  P3  P4        (pompes péristaltiques)
    │   │   │   │
   R1  R2  R3  R4  ── tuyaux ──► verre
```

Le bouton d'arrêt d'urgence coupe l'alimentation 12 V des pompes, indépendamment du programme.

## Structure du dépôt (proposition)

```
Projet-Integration/
├── README.md
├── CAHIER_DES_CHARGES.md
├── docs/          schémas (architecture, hydraulique, électrique), procédures
├── firmware/      code du Pico W (pompes, séquenceur, LED, serveur web)
├── web/           page web (mode user et mode admin)
├── data/          recettes des cocktails (JSON)
└── hardware/      liste du matériel (BOM), photos du montage
```

## Gestion de projet

- Dépôt : `Zdf667/Projet-Integration`
- Suivi : GitHub Project (board Todo / In Progress / Done) alimenté par des issues.
- Organisation : 7 epics (0 à 6) et 22 user stories, réparties en Sprint 1, Sprint 2, Sprint 3 et Démo.
- Les tâches techniques sont étiquetées `HW` (matériel), `SW` (logiciel), `DOC` (documentation) et `TEST`.

## État d'avancement

- [x] Découpage en epics et user stories
- [x] Issues créées dans GitHub et ajoutées au board
- [x] Liste du matériel établie
- [ ] Schémas (architecture, hydraulique, électrique)
- [ ] Commande du matériel
- [ ] Banc de test d'une pompe
- [ ] Firmware et page web

## Équipe

| Nom | Rôle |
|---|---|
| *à compléter* | |

## Points à décider

- Mode Wi-Fi : le Pico crée son propre réseau, ou rejoint le Wi-Fi de l'école ou de la maison.
- Langage du firmware (MicroPython ou C/C++).
- Conservation du bouton d'arrêt d'urgence physique (recommandé).
