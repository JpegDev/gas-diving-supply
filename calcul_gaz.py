# calcul_gaz.py

class CalculateurMelange:
    """
    Calcul par la méthode des pressions partielles
    
    Principe : On part de ce qu'il y a dans la bouteille
               et on calcule ce qu'il faut AJOUTER
    """
    
    def calculer_remplissage(
        self,
        # État actuel bouteille
        pression_actuelle: float,    # bar
        o2_actuel: float,            # % ex: 21.0
        he_actuel: float,            # % ex: 0.0
        capacite_bouteille: float,   # litres ex: 12.0
        
        # Objectif
        pression_cible: float,       # bar ex: 200
        o2_cible: float,             # % ex: 32.0
        he_cible: float,             # % ex: 0.0
    ) -> dict:
        
        n2_actuel = 100 - o2_actuel - he_actuel
        n2_cible  = 100 - o2_cible  - he_cible
        
        # Volume total final en bar·litres
        vol_final_bl = pression_cible * capacite_bouteille
        # Volume actuel en bar·litres
        vol_actuel_bl = pression_actuelle * capacite_bouteille
        
        # Quantités finales souhaitées (bar·litres de chaque gaz)
        o2_final_bl  = vol_final_bl * (o2_cible / 100)
        he_final_bl  = vol_final_bl * (he_cible / 100)
        n2_final_bl  = vol_final_bl * (n2_cible / 100)
        
        # Quantités actuelles
        o2_actuel_bl = vol_actuel_bl * (o2_actuel / 100)
        he_actuel_bl = vol_actuel_bl * (he_actuel / 100)
        n2_actuel_bl = vol_actuel_bl * (n2_actuel / 100)
        
        # Ce qu'il faut AJOUTER
        o2_a_ajouter  = o2_final_bl  - o2_actuel_bl
        he_a_ajouter  = he_final_bl  - he_actuel_bl
        n2_a_ajouter  = n2_final_bl  - n2_actuel_bl
        
        # L'azote vient avec l'air (air = 21% O2, 79% N2)
        # Si on ajoute de l'air : on apporte O2 + N2 ensemble
        # Méthode : d'abord He pur, puis O2 pur, puis compléter à l'air
        
        # Quantité d'air nécessaire pour apporter le N2 manquant
        # (l'air contient 79% de N2)
        air_a_ajouter_bl = n2_a_ajouter / 0.79  # bar·litres d'air
        
        # L'air apporte aussi de l'O2 (21%)
        o2_apporte_par_air = air_a_ajouter_bl * 0.21
        
        # L'O2 pur à ajouter = O2 manquant - O2 apporté par l'air
        o2_pur_a_ajouter = o2_a_ajouter - o2_apporte_par_air
        
        # Vérifications
        warnings = []
        if o2_pur_a_ajouter < 0:
            warnings.append(
                "⚠️ Trop d'O2 avec l'air seul - envisager de purger la bouteille"
            )
        if he_a_ajouter < 0:
            warnings.append("⚠️ Trop d'hélium - purge nécessaire")
        if air_a_ajouter_bl < 0:
            warnings.append("⚠️ Trop d'azote - purge partielle nécessaire")
            
        return {
            "o2_pur_bl":   round(max(0, o2_pur_a_ajouter), 2),
            "he_pur_bl":   round(max(0, he_a_ajouter), 2),
            "air_bl":      round(max(0, air_a_ajouter_bl), 2),
            "total_ajoute_bl": round(
                max(0, o2_pur_a_ajouter) + 
                max(0, he_a_ajouter) + 
                max(0, air_a_ajouter_bl), 2
            ),
            "warnings": warnings,
            # Pour vérification
            "o2_final_theorique": round(
                (o2_actuel_bl + max(0, o2_pur_a_ajouter) + 
                 max(0, air_a_ajouter_bl) * 0.21) / vol_final_bl * 100, 1
            ),
        }
    
    def verifier_stock_suffisant(
        self, 
        besoins: list[dict], 
        stock: dict
    ) -> dict:
        """
        besoins : liste de résultats calculer_remplissage()
        stock   : {"o2_bl": 5000, "he_bl": 2000, "air_bl": 50000}
        """
        total_o2  = sum(b["o2_pur_bl"] for b in besoins)
        total_he  = sum(b["he_pur_bl"] for b in besoins)
        total_air = sum(b["air_bl"]    for b in besoins)
        
        return {
            "o2":  {"besoin": total_o2,  "stock": stock["o2_bl"],  
                    "ok": stock["o2_bl"]  >= total_o2},
            "he":  {"besoin": total_he,  "stock": stock["he_bl"],  
                    "ok": stock["he_bl"]  >= total_he},
            "air": {"besoin": total_air, "stock": stock["air_bl"], 
                    "ok": stock["air_bl"] >= total_air},
        }
