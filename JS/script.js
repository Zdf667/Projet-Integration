// 1. Les cocktails. "point" = couleur des ronds, "liquide" = couleur du verre
const cocktails = [
  { nom: "Grenadine plate", icone: "🍹", couleur: "#ff9a98", point: "#e8334f", liquide: "linear-gradient(#ff8a8a, #ff5a6e)", description: "Douce, rouge et toute simple.", ingredients: ["Sirop de grenadine", "Eau plate"] },
  { nom: "Grenadine soda", icone: "🧋", couleur: "#ffdd57", point: "#e8334f", liquide: "linear-gradient(#ff8a8a, #ff5a6e)", description: "Le même fruité, avec des bulles.", ingredients: ["Sirop de grenadine", "Eau gazeuse"] },
  { nom: "Menthe plate", icone: "🧃", couleur: "#74e0c4", point: "#1fa37f", liquide: "linear-gradient(#6ee7c4, #2bbd96)", description: "Un splash frais et tout doux.", ingredients: ["Sirop de menthe", "Eau plate"] },
  { nom: "Menthe soda", icone: "🍸", couleur: "#74b8ff", point: "#1fa37f", liquide: "linear-gradient(#6ee7c4, #2bbd96)", description: "Fraîcheur maximale, bulles incluses.", ingredients: ["Sirop de menthe", "Eau gazeuse"] },
  { nom: "Eau gazeuse", icone: "🫧", couleur: "#ddd6ff", point: "#6a5acd", liquide: "linear-gradient(#c9c2ff, #8f84f0)", description: "La pause pétillante par excellence.", ingredients: ["Eau gazeuse"] },
  { nom: "Eau plate", icone: "💧", couleur: "#fff8e6", point: "#3f8ee8", liquide: "linear-gradient(#a8d4ff, #5aa5f0)", description: "Simple, pure, toujours une bonne idée.", ingredients: ["Eau plate"] }
];

// 2. On récupère les éléments de la page
const ecranListe = document.getElementById("ecran-liste");
const ecranChoix = document.getElementById("ecran-choix");
const ecranMixage = document.getElementById("ecran-mixage");
const liste = document.getElementById("liste");
const carteChoix = document.getElementById("carte-choix");
const choixNom = document.getElementById("choix-nom");
const choixIngredients = document.getElementById("choix-ingredients");
const liquide = document.getElementById("liquide");
const mixageTitre = document.getElementById("mixage-titre");
const mixageTexte = document.getElementById("mixage-texte");
const boutonRetour = document.getElementById("bouton-retour");

let cocktailChoisi = null;

// 3. Fonction pour montrer un seul écran à la fois
function afficherEcran(ecran) {
  ecranListe.classList.add("cache");
  ecranChoix.classList.add("cache");
  ecranMixage.classList.add("cache");
  ecran.classList.remove("cache");
}

// 4. On crée les cartes de la liste
cocktails.forEach(function (cocktail) {
  const carte = document.createElement("button");
  carte.className = "carte";
  carte.style.background = cocktail.couleur;
  carte.innerHTML =
    '<div class="carte-icone">' + cocktail.icone + "</div>" +
    "<h3>" + cocktail.nom + "</h3>" +
    "<p>" + cocktail.description + "</p>";

  carte.addEventListener("click", function () {
    choisirCocktail(cocktail);
  });
  liste.appendChild(carte);
});

// 5. Écran du choix : nom + ingrédients
function choisirCocktail(cocktail) {
  cocktailChoisi = cocktail;
  carteChoix.style.background = cocktail.couleur;
  choixNom.textContent = cocktail.nom;

  choixIngredients.innerHTML = "";
  cocktail.ingredients.forEach(function (ingredient) {
    const li = document.createElement("li");
    li.innerHTML = '<span class="point" style="background:' + cocktail.point + '"></span>' + ingredient;
    choixIngredients.appendChild(li);
  });

  afficherEcran(ecranChoix);
}

// 6. Bouton "Changer de mix" : retour à la liste
document.getElementById("bouton-changer").addEventListener("click", function () {
  afficherEcran(ecranListe);
});

// 7. Bouton "Préparer le cocktail" : animation de chargement
document.getElementById("bouton-preparer").addEventListener("click", function () {
  // On remet l'écran à zéro
  mixageTitre.textContent = "Ça mixe, ça pétille...";
  mixageTexte.textContent = "Ton verre se remplit de bonne humeur. Encore une petite seconde !";
  boutonRetour.classList.add("cache");
  liquide.style.transition = "none";
  liquide.style.height = "0";
  liquide.style.background = cocktailChoisi.liquide;

  afficherEcran(ecranMixage);

  // Petite pause puis le verre se remplit (3 secondes)
  setTimeout(function () {
    liquide.style.transition = "height 3s ease-in-out";
    liquide.style.height = "75%";
  }, 50);

  // Au bout de 3,5 secondes : c'est prêt !
  setTimeout(function () {
    mixageTitre.textContent = "C'est prêt !";
    mixageTexte.textContent = "Ton mix est servi. Profite de la fraîcheur et fais tourner les bonnes vibes !";
    boutonRetour.classList.remove("cache");
  }, 3500);
});

// 8. Bouton "Retour" : on revient à la liste
boutonRetour.addEventListener("click", function () {
  afficherEcran(ecranListe);
});