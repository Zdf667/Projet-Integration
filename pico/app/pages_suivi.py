# US4.2 – Page de SUIVI de la préparation : avancement, verre prêt (+ conseil de service, US2.4), arrêt.
from app import conseil
from app.pages import e, fin, haut


_LIBELLES = {"attente": "Machine prête", "en_cours": "Préparation en cours", "termine": "Terminé", "erreur": "Arrêt ou erreur"}


def _script_suivi(etat):
    """Interroge /status chaque seconde ; recharge la page quand l'état change."""
    if etat["etat"] != "en_cours":
        return ""
    return ('<script>var e0="en_cours";setInterval(function(){fetch("/status").then(function(r){return r.json()})'
            '.then(function(s){if(s.etat!==e0){location.reload();return}'
            'document.getElementById("p").value=s.pct;document.getElementById("m").textContent=s.message;'
            'document.getElementById("n").textContent=s.pct+" %"}).catch(function(){})},1000)</script>')


def _bloc_progression(etat):
    return ('<div class="suivi"><progress id="p" max="100" value="{}"></progress><b id="n">{} %</b></div>'
            '<p id="m" class="msg ok" role="status">{}</p>').format(etat["pct"], etat["pct"], e(etat["message"]))


def page_suivi(etat):
    """US4.2 – Avancement de la préparation, verre prêt et conseil de service (US2.4)."""
    refresh = '<noscript><meta http-equiv="refresh" content="2"></noscript>' if etat["etat"] == "en_cours" else ""
    h = haut("user", extra_head=refresh)
    h.append('<section><h2>' + e(etat["titre"] or _LIBELLES.get(etat["etat"], "")) + '</h2>')
    if etat["etat"] == "en_cours":
        h.append(_bloc_progression(etat))
        h.append('<form method="post" action="/arreter"><button type="submit" class="danger">Arrêter</button></form>')
    elif etat["etat"] == "termine":
        h.append('<p class="msg ok grand" role="status">' + e(etat["message"]) + ' !</p>')
        h.append(conseil.html(etat["conseil"]))
        h.append('<script>if(navigator.vibrate)navigator.vibrate([200,100,200])</script>')
        h.append('<form method="post" action="/acquitter"><button type="submit">Retour aux cocktails</button></form>')
    elif etat["etat"] == "erreur":
        h.append('<p class="msg err" role="alert">' + e(etat["message"]) + '</p>')
        h.append('<form method="post" action="/acquitter"><button type="submit">Retour aux cocktails</button></form>')
    else:
        h.append('<p class="indice">Aucune préparation en cours.</p><p><a class="bouton" href="/">Voir les cocktails</a></p>')
    h.append('</section>')
    h.append(_script_suivi(etat))
    return fin(h)
