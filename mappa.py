"""
Tyche · dalle categorie di Overture ai tag di OpenStreetMap (27 set 2026)
--------------------------------------------------------------------------
Overture classifica i posti con `taxonomy.primary` (1.813 valori in Italia,
release 2026-09-23.1). L'app cerca i posti vicini con i FILTRI della mappa
(`src/lib/osmPlaces.ts`: `["amenity"="pharmacy"]`, `["craft"="plumber"]`…),
e `lib/overture.ts` li applica tali e quali anche a Overture. Qui si traduce
ogni valore di Overture nei tag OSM equivalenti, così un solo vocabolario
vale per tutte e due le fonti.

REGOLE:
  · solo i valori che corrispondono a un tag che l'app CERCA davvero (i tag
    dei filtri: il test `mappa.test` lo verifica) — il resto non entra nei
    file, e i file restano piccoli;
  · un valore può dare più tag («pizza_restaurant» è un ristorante E ha la
    cucina pizza: la farmacia di un filtro generico e la pizzeria di uno
    specifico devono trovarlo entrambe);
  · nel dubbio, niente: un posto mancante costa meno di un posto sbagliato
    («professional_service», «b2b_service», «shopping» non dicono il mestiere).
"""

R = "amenity=restaurant"

TAX_A_OSM: dict[str, list[str]] = {
    # --- mangiare e bere -------------------------------------------------------
    "restaurant": [R], "italian_restaurant": [R], "mediterranean_restaurant": [R], "european_restaurant": [R],
    "bistro": [R], "diner": [R], "comfort_food_restaurant": [R], "buffet_restaurant": [R], "theme_restaurant": [R],
    "piadina_restaurant": [R, "amenity=fast_food"], "breakfast_and_brunch_restaurant": [R, "amenity=cafe"],
    "pizza_restaurant": [R, "cuisine=pizza"], "pizza_delivery_service": ["cuisine=pizza", "amenity=fast_food"],
    "seafood_restaurant": [R, "cuisine=seafood"], "sushi_restaurant": [R, "cuisine=sushi", "cuisine=japanese"],
    "japanese_restaurant": [R, "cuisine=japanese"], "ramen_restaurant": [R, "cuisine=ramen", "cuisine=japanese"],
    "chinese_restaurant": [R, "cuisine=chinese"], "asian_restaurant": [R], "asian_fusion_restaurant": [R],
    "indian_restaurant": [R, "cuisine=indian"], "thai_restaurant": [R, "cuisine=thai"],
    "mexican_restaurant": [R, "cuisine=mexican"], "latin_american_restaurant": [R], "peruvian_restaurant": [R, "cuisine=peruvian"],
    "brazilian_restaurant": [R], "argentine_restaurant": [R, "cuisine=steak_house"],
    "greek_restaurant": [R, "cuisine=greek"], "spanish_restaurant": [R, "cuisine=spanish"], "tapas_bar": [R, "cuisine=tapas", "cuisine=spanish"],
    "german_restaurant": [R, "cuisine=german"], "american_restaurant": [R, "cuisine=american"],
    "turkish_restaurant": [R, "cuisine=kebab"], "doner_kebab_restaurant": ["amenity=fast_food", "cuisine=kebab"],
    "middle_eastern_restaurant": [R, "cuisine=middle_eastern", "cuisine=lebanese"], "falafel_restaurant": ["amenity=fast_food", "cuisine=middle_eastern", "cuisine=lebanese"],
    "poke_restaurant": [R, "cuisine=poke"], "vegetarian_restaurant": [R, "cuisine=vegetarian"], "vegan_restaurant": [R, "cuisine=vegan"],
    "gluten_free_restaurant": [R, "diet:gluten_free=yes"],
    "steakhouse": [R, "cuisine=steak_house", "cuisine=meat"], "barbecue_restaurant": [R, "cuisine=barbecue", "cuisine=bbq", "cuisine=grill"],
    "bar_and_grill_restaurant": [R, "cuisine=grill"], "burger_restaurant": ["amenity=fast_food", "cuisine=burger"],
    "chicken_restaurant": ["amenity=fast_food", "cuisine=chicken"], "sandwich_shop": ["amenity=fast_food", "cuisine=burger"],
    "fast_food_restaurant": ["amenity=fast_food"], "food_truck_stand": ["amenity=fast_food"], "food_court": ["amenity=fast_food"],
    "cafeteria": [R], "pancake_house": ["amenity=cafe"],
    "bar": ["amenity=bar"], "cocktail_bar": ["amenity=bar"], "wine_bar": ["amenity=bar"], "beer_bar": ["amenity=pub"], "lounge": ["amenity=bar"],
    "sports_bar": ["amenity=bar"], "dive_bar": ["amenity=bar"], "hotel_bar": ["amenity=bar"], "speakeasy": ["amenity=bar"], "hookah_bar": ["amenity=bar"],
    "pub": ["amenity=pub"], "gastropub": ["amenity=pub"], "irish_pub": ["amenity=pub"], "beer_garden": ["amenity=pub"], "bar_tabac": ["amenity=bar", "shop=tobacco"],
    "cafe": ["amenity=cafe"], "coffee_shop": ["amenity=cafe"], "tea_room": ["amenity=cafe"], "smoothie_juice_bar": ["amenity=cafe"], "bubble_tea_shop": ["amenity=cafe"],
    "ice_cream_shop": ["amenity=ice_cream", "shop=ice_cream"], "gelato_shop": ["amenity=ice_cream", "shop=ice_cream"], "frozen_yogurt_shop": ["amenity=ice_cream"],
    "dance_club": ["amenity=nightclub"], "nightlife_venue": ["amenity=nightclub"],
    # le cucine che mancavano (28 set 2026: l'owner era da «Panda», coreano, e Tyche non lo trovava —
    # Overture lo aveva come korean_restaurant, questa tabella no)
    "korean_restaurant": [R, "cuisine=korean"], "vietnamese_restaurant": [R, "cuisine=vietnamese"], "french_restaurant": [R, "cuisine=french"],
    "lebanese_restaurant": [R, "cuisine=lebanese", "cuisine=middle_eastern"], "arabian_restaurant": [R, "cuisine=middle_eastern"],
    "syrian_restaurant": [R, "cuisine=middle_eastern"], "persian_restaurant": [R, "cuisine=middle_eastern"], "egyptian_restaurant": [R, "cuisine=middle_eastern"],
    "ethiopian_restaurant": [R, "cuisine=ethiopian", "cuisine=eritrean"], "hawaiian_restaurant": [R, "cuisine=hawaiian", "cuisine=poke"],
    "indonesian_restaurant": [R, "cuisine=indonesian"], "malaysian_restaurant": [R, "cuisine=malaysian"],
    "texmex_restaurant": [R, "cuisine=mexican"], "taco_restaurant": ["amenity=fast_food", "cuisine=mexican"],
    "hot_dog_restaurant": ["amenity=fast_food", "cuisine=american"], "southern_american_restaurant": [R, "cuisine=american"],
    "chicken_wings_restaurant": ["amenity=fast_food", "cuisine=chicken", "cuisine=american"], "meat_restaurant": [R, "cuisine=meat"],
    "fish_restaurant": [R, "cuisine=seafood"], "fish_and_chips_restaurant": ["amenity=fast_food", "cuisine=seafood"],
    "dim_sum_restaurant": [R, "cuisine=chinese"], "dumpling_restaurant": [R, "cuisine=chinese"], "cantonese_restaurant": [R, "cuisine=chinese"],
    "sichuan_restaurant": [R, "cuisine=chinese"], "taiwanese_restaurant": [R, "cuisine=chinese"], "wok_restaurant": [R, "cuisine=chinese"],
    "pakistani_restaurant": [R, "cuisine=indian"], "bangladeshi_restaurant": [R, "cuisine=indian"], "sri_lankan_restaurant": [R, "cuisine=indian"],
    "halal_restaurant": [R, "diet:halal=yes"], "kosher_restaurant": [R, "diet:kosher=yes"],
    "beach_bar": ["amenity=bar"], "whiskey_bar": ["amenity=bar"], "tiki_bar": ["amenity=bar"], "piano_bar": ["amenity=bar"],
    "champagne_bar": ["amenity=bar"], "sake_bar": ["amenity=bar"], "gay_bar": ["amenity=bar"],
    # --- la spesa -----------------------------------------------------------------
    "grocery_store": ["shop=supermarket", "shop=convenience"], "convenience_store": ["shop=convenience"],
    # «warehouse_club_store» NO: in Italia sono grossisti (Metro, cash and carry, ingrosso) — non si fa la spesa lì
    "superstore": ["shop=supermarket"], "discount_store": ["shop=supermarket"], "organic_grocery_store": ["shop=organic", "shop=supermarket"],
    "ethical_grocery_store": ["shop=organic"], "health_food_store": ["shop=organic", "shop=nutrition_supplements"],
    "bakery": ["shop=bakery"], "patisserie_cake_shop": ["shop=pastry", "shop=bakery"], "custom_cakes_shop": ["shop=pastry"], "cupcake_shop": ["shop=pastry"], "dessert_shop": ["shop=pastry"],
    "butcher_shop": ["shop=butcher"], "fishmonger": ["shop=seafood"], "seafood_market": ["shop=seafood"],
    "produce_store": ["shop=greengrocer"], "greengrocer": ["shop=greengrocer"], "cheese_shop": ["shop=cheese"], "dairy_store": ["shop=dairy"],
    "delicatessen": ["shop=deli"], "specialty_foods_store": ["shop=deli"], "pasta_store": ["shop=deli"], "olive_oil_store": ["shop=deli"],
    "frozen_foods_store": ["shop=frozen_food"], "candy_store": ["shop=confectionery"], "chocolatier": ["shop=chocolate", "shop=confectionery"],
    "liquor_store": ["shop=alcohol"], "beer_wine_spirits_store": ["shop=alcohol", "shop=wine"], "winery": ["craft=winery", "shop=wine"],
    "tobacco_shop": ["shop=tobacco"], "smoke_and_vape_store": ["shop=e-cigarette", "shop=tobacco"], "newspaper_and_magazines_store": ["shop=newsagent"],
    "farmers_market": ["amenity=marketplace"], "flea_market": ["amenity=marketplace"], "honey_farm_shop": ["shop=farm"], "farm": ["shop=farm"],
    "vitamin_and_supplement_store": ["shop=nutrition_supplements"], "herb_and_spice_store": ["shop=herbalist"],
    "caterer": ["craft=caterer"],
    # --- salute ----------------------------------------------------------------------
    "pharmacy": ["amenity=pharmacy"], "drugstore": ["shop=chemist"],
    "dental_clinic": ["amenity=dentist", "healthcare=dentist"], "general_dentistry": ["amenity=dentist", "healthcare=dentist"], "cosmetic_dentistry": ["amenity=dentist", "healthcare=dentist"],
    "pediatric_dentistry": ["amenity=dentist", "healthcare=dentist"], "prosthodontics": ["amenity=dentist", "healthcare=dentist"],
    "orthodontics": ["amenity=dentist", "healthcare=dentist", "healthcare:speciality=orthodontics"],
    "doctors_office": ["amenity=doctors", "healthcare=doctor"], "family_practice": ["amenity=doctors", "healthcare=doctor"], "health_care": ["amenity=clinic"],
    "outpatient_care_facility": ["amenity=clinic", "healthcare=centre"], "public_health_clinic": ["amenity=clinic"], "medical_service_organization": ["amenity=clinic"],
    "hospital": ["amenity=hospital"], "emergency_department": ["amenity=hospital"], "urgent_care_clinic": ["amenity=clinic"],
    "laboratory": ["healthcare=laboratory"], "laboratory_testing": ["healthcare=laboratory"], "diagnostic_imaging": ["healthcare:speciality=radiology"], "radiology": ["healthcare:speciality=radiology"],
    "psychology": ["healthcare=psychotherapist"], "psychotherapy": ["healthcare=psychotherapist"], "counseling": ["healthcare=psychotherapist"], "family_counseling": ["healthcare=psychotherapist"],
    "psychiatry": ["healthcare:speciality=psychiatry"], "child_psychiatry": ["healthcare:speciality=psychiatry"],
    "physical_therapy": ["healthcare=physiotherapist"], "rehabilitation_center": ["healthcare=rehabilitation"], "osteopathic_medicine": ["healthcare:speciality=osteopathy"],
    "chiropractic": ["healthcare:speciality=chiropractic"], "acupuncture": ["healthcare:speciality=acupuncture"], "podiatry": ["healthcare=podiatrist"],
    "speech_therapy": ["healthcare=speech_therapist"], "nutrition_service": ["healthcare=nutrition_counselling"],
    "pediatric_clinic": ["healthcare:speciality=paediatrics"], "obstetrics_and_gynecology": ["healthcare:speciality=gynaecology"],
    "dermatology": ["healthcare:speciality=dermatology"], "cardiology": ["healthcare:speciality=cardiology"], "ophthalmology": ["healthcare:speciality=ophthalmology"],
    "otolaryngology": ["healthcare:speciality=otolaryngology"], "ear_nose_and_throat": ["healthcare:speciality=otolaryngology"],
    "orthopedic_surgery": ["healthcare:speciality=orthopaedics"], "orthopedics": ["healthcare:speciality=orthopaedics"], "urology": ["healthcare:speciality=urology"],
    "neurology": ["healthcare:speciality=neurology"], "plastic_and_reconstructive_surgery": ["healthcare=plastic_surgery"],
    "eyewear_store": ["shop=optician"], "optometry": ["shop=optician"], "hearing_aid_store": ["shop=hearing_aids"], "audiology": ["shop=hearing_aids"],
    "medical_supply_store": ["shop=medical_supply"], "orthopedic_shoe_store": ["shop=medical_supply"],
    "retirement_home": ["amenity=nursing_home"], "assisted_living_facility": ["amenity=nursing_home"],
    "veterinarian": ["amenity=veterinary"], "veterinary_care": ["amenity=veterinary"], "animal_hospital": ["amenity=veterinary"], "emergency_pet_hospital": ["amenity=veterinary"],
    # --- casa, lavori, artigiani ----------------------------------------------------------
    "plumbing": ["craft=plumber"], "electrician": ["craft=electrician"], "key_and_locksmith": ["shop=locksmith", "craft=locksmith"],
    "hvac_service": ["craft=hvac"], "roofing": ["craft=roofer"], "carpenter": ["craft=carpenter"], "painting": ["craft=painter"],
    "tiling": ["craft=tiler"], "flooring_contractor": ["craft=tiler"], "glass_and_mirror_sales_service": ["craft=glaziery"],
    "windows_installation": ["craft=window_construction"], "window_supplier": ["craft=window_construction"],
    "contractor": ["craft=builder"], "building_contractor": ["craft=builder"], "building_or_construction_service": ["craft=builder"],
    "masonry_contractor": ["craft=builder", "craft=stonemason"], "masonry_concrete": ["craft=builder"], "handyman": ["craft=builder"],
    "bathroom_remodeling": ["craft=builder"], "altering_and_remodeling_contractor": ["craft=builder"],
    "marble_and_granite_professional": ["craft=stonemason"], "blacksmith": ["craft=blacksmith"], "iron_fabricator": ["craft=metal_construction"],
    "metal_fabricator": ["craft=metal_construction"], "steel_fabricator": ["craft=metal_construction"], "welder": ["craft=metal_construction"],
    "furniture_reupholstery": ["craft=upholsterer"], "chimney_sweep": ["craft=chimney_sweeper"], "fireplace_service": ["shop=fireplace", "craft=chimney_sweeper"],
    "gardener": ["craft=gardener"], "landscaping": ["craft=gardener"], "tree_service": ["craft=gardener"],
    "cleaning_service": ["craft=cleaning"], "home_cleaning": ["craft=cleaning"], "office_cleaning": ["craft=cleaning"], "janitorial_service": ["craft=cleaning"],
    "mover": ["office=moving_company"], "pest_control_service": ["craft=cleaning"],
    "appliance_repair_service": ["craft=electronics_repair"], "electronics_repair_shop": ["craft=electronics_repair"], "mobile_phone_repair": ["craft=electronics_repair", "shop=mobile_phone"],
    "it_service_and_computer_repair": ["shop=computer", "craft=electronics_repair"], "computer_store": ["shop=computer"],
    "tailor": ["craft=tailor"], "sewing_and_alterations": ["craft=tailor"], "shoe_repair": ["shop=shoe_repair", "craft=shoemaker"],
    "photography_service": ["craft=photographer"], "event_photography_service": ["craft=photographer"],
    "sign_making": ["craft=signmaker"], "framing_store": ["shop=frame", "craft=framing"], "goldsmith": ["shop=jewelry"],
    "security_service": ["office=security"], "security_systems": ["office=security"],
    "dry_cleaning": ["shop=dry_cleaning"], "laundry_service": ["shop=laundry", "shop=dry_cleaning"], "laundromat": ["shop=laundry"],
    # --- auto, moto, bici ------------------------------------------------------------------
    "automotive_repair": ["shop=car_repair"], "auto_body_shop": ["shop=car_repair"], "auto_electrical_repair": ["shop=car_repair"],
    "engine_repair_service": ["shop=car_repair"], "truck_repair": ["shop=car_repair"], "auto_glass_service": ["shop=car_repair"],
    "mobile_dent_repair": ["shop=car_repair"], "auto_restoration_service": ["shop=car_repair"], "auto_upholstery": ["shop=car_repair"],
    "tire_dealer_and_repair": ["shop=tyres", "shop=car_repair"], "tire_shop": ["shop=tyres"],
    "car_wash": ["amenity=car_wash"], "auto_detailing": ["amenity=car_wash"], "auto_parts_store": ["shop=car_parts"],
    "auto_dealer": ["shop=car"], "used_auto_dealer": ["shop=car"], "motorcycle_dealer": ["shop=motorcycle"], "motorcycle_repair": ["shop=motorcycle_repair", "shop=motorcycle"],
    "motorcycle_parts_store": ["shop=motorcycle"], "bike_store": ["shop=bicycle"], "bike_repair_maintenance": ["shop=bicycle"],
    "gas_station": ["amenity=fuel"], "truck_gas_station": ["amenity=fuel"], "ev_charging_station": ["amenity=charging_station"],
    "car_rental_service": ["amenity=car_rental"], "bike_rental": ["amenity=bicycle_rental"], "boat_rental_and_training": ["amenity=boat_rental"], "boat_hire_service": ["amenity=boat_rental"],
    "driving_school": ["amenity=driving_school"], "emissions_inspection": ["amenity=vehicle_inspection"], "department_of_motor_vehicles": ["amenity=vehicle_inspection"],
    "parking": ["amenity=parking"], "parking_garage": ["amenity=parking"], "taxi_service": ["amenity=taxi"], "taxi_stand": ["amenity=taxi"],
    "recreational_vehicle_dealer": ["shop=caravan"], "boat_dealer": ["shop=boat"], "boat_parts_store": ["shop=boat"],
    # --- professioni, uffici ----------------------------------------------------------------
    "attorney_or_law_firm": ["office=lawyer"], "legal_service": ["office=lawyer"], "criminal_defense_law": ["office=lawyer"], "divorce_and_family_law": ["office=lawyer"],
    "employment_law": ["office=lawyer"], "immigration_law": ["office=lawyer"], "notary_public": ["office=notary"],
    "accountant": ["office=accountant"], "bookkeeper": ["office=accountant"], "tax_service": ["office=tax_advisor", "office=accountant"],
    "insurance_agency": ["office=insurance"], "auto_insurance": ["office=insurance"], "financial_advising": ["office=financial_advisor"],
    "bank": ["amenity=bank"], "bank_or_credit_union": ["amenity=bank"], "credit_union": ["amenity=bank"], "atm": ["amenity=atm"],
    "money_transfer_service": ["shop=money_transfer"], "gold_buyer": ["shop=pawnbroker"],
    "real_estate_agent": ["office=estate_agent"], "real_estate_service": ["office=estate_agent"], "apartment_agent": ["office=estate_agent"], "property_management": ["office=property_management"],
    "architect": ["office=architect"], "architectural_designer": ["office=architect"], "landscape_architect": ["office=architect"],
    "engineering_service": ["office=engineer"], "civil_engineer": ["office=engineer"], "structural_engineer": ["office=engineer"], "mechanical_engineer": ["office=engineer"],
    "information_technology_company": ["office=it"], "software_development": ["office=it"], "it_consultant": ["office=it"], "web_designer": ["office=it"],
    "e_commerce_service": ["office=it"], "web_hosting_service": ["office=it"],
    "advertising_agency": ["office=advertising_agency"], "marketing_agency": ["office=advertising_agency"], "internet_marketing_service": ["office=advertising_agency"],
    "social_media_agency": ["office=advertising_agency"], "graphic_designer": ["office=graphic_design"], "printing_service": ["shop=copyshop"],
    "commercial_printer": ["shop=copyshop"], "t_shirt_printing_service": ["shop=copyshop"], "3d_printing_service": ["shop=copyshop"],
    "employment_agency": ["office=employment_agency"], "coworking_space": ["amenity=coworking_space", "office=coworking"],
    "freight_and_cargo_service": ["office=logistics"], "courier_and_delivery_service": ["office=logistics"], "shipping_center": ["office=logistics"],
    "travel_agent": ["shop=travel_agency"], "travel_service": ["shop=travel_agency"], "tour_operator": ["shop=travel_agency"],
    "funeral_service": ["shop=funeral_directors"], "cremation_service": ["shop=funeral_directors"],
    "post_office": ["amenity=post_office"], "police_station": ["amenity=police"], "fire_station": ["amenity=fire_station"], "town_hall": ["amenity=townhall"],
    "government_office": ["office=government"], "courthouse": ["amenity=courthouse"], "embassy": ["amenity=embassy", "office=diplomatic"],
    # --- persona, bellezza, sport --------------------------------------------------------------
    "hair_salon": ["shop=hairdresser"], "barber": ["shop=hairdresser"], "hair_stylist": ["shop=hairdresser"],
    "beauty_salon": ["shop=beauty"], "nail_salon": ["shop=beauty"], "esthetician": ["shop=beauty"], "skin_care_and_makeup": ["shop=beauty"], "laser_hair_removal": ["shop=beauty"],
    "makeup_artist": ["shop=beauty"], "tanning_salon": ["leisure=tanning_salon"], "massage_therapy": ["shop=massage"], "day_spa": ["leisure=spa"], "health_spa": ["leisure=spa"],
    "spa": ["leisure=spa"], "medical_spa": ["leisure=spa"], "tattoo_and_piercing": ["shop=tattoo"], "tattoo": ["shop=tattoo"], "piercing": ["shop=tattoo"],
    "gym": ["leisure=fitness_centre"], "fitness_trainer": ["leisure=fitness_centre"], "pilates_studio": ["leisure=fitness_centre"], "yoga_studio": ["leisure=fitness_centre"],
    "boxing_gym": ["leisure=fitness_centre"], "martial_arts_club": ["leisure=sports_centre"], "sports_complex": ["leisure=sports_centre"], "swimming_pool": ["leisure=swimming_pool"],
    "dance_studio": ["amenity=dancing_school"], "music_school": ["amenity=music_school"], "language_school": ["amenity=language_school"],
    "bowling_alley": ["leisure=bowling_alley"], "escape_room": ["leisure=escape_game"], "golf_course": ["leisure=golf_course"],
    "horse_riding": ["leisure=horse_riding"], "horseback_riding_service": ["leisure=horse_riding"], "equestrian_facility": ["leisure=horse_riding"],
    "shooting_range": ["leisure=shooting_range"], "ice_skating_rink": ["leisure=ice_rink"], "skate_park": ["leisure=skatepark"],
    "scuba_diving_center": ["shop=scuba_diving"], "diving_center": ["shop=scuba_diving"], "recording_and_rehearsal_studio": ["studio=audio"],
    "pet_store": ["shop=pet"], "pet_groomer": ["shop=pet_grooming"], "pet_boarding": ["amenity=animal_boarding"], "animal_shelter": ["amenity=animal_shelter"],
    "child_care_and_day_care": ["amenity=childcare", "amenity=kindergarten"], "day_care_preschool": ["amenity=kindergarten"], "preschool": ["amenity=kindergarten"],
    # --- negozi -----------------------------------------------------------------------------------------
    "clothing_store": ["shop=clothes"], "womens_clothing_store": ["shop=clothes"], "mens_clothing_store": ["shop=clothes"], "childrens_clothing_store": ["shop=clothes"],
    "fashion_boutique": ["shop=clothes"], "fashion_and_apparel_store": ["shop=clothes"], "second_hand_clothing_store": ["shop=clothes", "shop=second_hand"],
    "lingerie_store": ["shop=clothes"], "sportswear_store": ["shop=clothes", "shop=sports"], "bridal_shop": ["shop=bridal"],
    "shoe_store": ["shop=shoes"], "jewelry_store": ["shop=jewelry"], "watch_store": ["shop=watches"],
    "hardware_store": ["shop=hardware", "shop=doityourself"], "home_improvement_store": ["shop=doityourself", "shop=hardware"], "building_supply_store": ["shop=doityourself", "shop=hardware"],
    "do_it_yourself_store": ["shop=doityourself"], "paint_store": ["shop=paint"], "electrical_supply_store": ["shop=electrical"], "lighting_store": ["shop=electrical"],
    "furniture_store": ["shop=furniture"], "mattress_store": ["shop=bed"], "home_goods_store": ["shop=houseware"], "kitchen_supply_store": ["shop=houseware"], "kitchen_and_bath_store": ["shop=kitchen"],
    "carpet_store": ["shop=carpet"], "linen_store": ["shop=houseware"], "window_treatment_store": ["shop=curtain"],
    "appliance_store": ["shop=appliance"], "electronics_store": ["shop=electronics"], "mobile_phone_store": ["shop=mobile_phone"], "mobile_phone_accessory_store": ["shop=mobile_phone"],
    "camera_and_photography_store": ["shop=photo"], "video_game_store": ["shop=video_games"], "music_and_dvd_store": ["shop=music"], "vinyl_record_store": ["shop=music"],
    "musical_instrument_store": ["shop=musical_instrument"], "bookstore": ["shop=books"], "comic_books_store": ["shop=books"],
    "business_office_supplies_and_stationery": ["shop=stationery"], "office_supply_store": ["shop=stationery"], "cards_and_stationery_store": ["shop=stationery"],
    "toy_store": ["shop=toys"], "baby_gear_and_nursery_store": ["shop=baby_goods"], "flowers_and_gifts_store": ["shop=florist", "shop=gift"], "florist": ["shop=florist"],
    "gift_shop": ["shop=gift"], "souvenir_store": ["shop=gift"], "party_supply_store": ["shop=party"], "costume_store": ["shop=party"],
    "cosmetics_and_fragrance_store": ["shop=cosmetics", "shop=perfumery"], "beauty_supply_store": ["shop=cosmetics"], "wig_store": ["shop=wigs"],
    "sporting_goods_store": ["shop=sports"], "hunting_and_fishing_store": ["shop=hunting", "shop=fishing"], "outdoor_store": ["shop=sports"],
    "nursery_and_gardening_store": ["shop=garden_centre"], "fabric_store": ["shop=fabric"], "knitting_supply_store": ["shop=wool"], "arts_crafts_and_hobby_store": ["shop=model"],
    "hobby_shop": ["shop=model"], "antique_store": ["shop=antiques"], "second_hand_store": ["shop=second_hand"], "betting_center": ["shop=bookmaker"], "lottery_vendor": ["shop=bookmaker"],
    "shopping_mall": ["shop=mall"], "department_store": ["shop=mall"], "farm_equipment_and_supply": ["shop=agrarian"], "livestock_feed_and_supply_store": ["shop=agrarian"],
    "cannabis_dispensary": ["shop=cannabis"], "pawn_shop": ["shop=pawnbroker"],
    # --- luoghi, cultura, trasporti -------------------------------------------------------------------
    "hotel": ["tourism=hotel"], "motel": ["tourism=hotel"], "hostel": ["tourism=hostel"], "guest_house": ["tourism=guest_house"], "bed_and_breakfast": ["tourism=guest_house"],
    "campground": ["tourism=camp_site"], "rv_park": ["tourism=caravan_site"], "museum": ["tourism=museum"], "art_museum": ["tourism=museum"], "history_museum": ["tourism=museum"],
    "art_gallery": ["tourism=gallery"], "zoo": ["tourism=zoo"], "aquarium": ["tourism=aquarium"], "amusement_park": ["tourism=theme_park"], "water_park": ["tourism=theme_park"],
    "movie_theater": ["amenity=cinema"], "theatre_venue": ["amenity=theatre"], "performing_arts_venue": ["amenity=theatre"], "library": ["amenity=library"],
    "train_station": ["railway=station"], "bus_station": ["amenity=bus_station"], "airport": ["aeroway=aerodrome"], "marina": ["harbour=yes"],
    "beach_resort": ["leisure=beach_resort"], "park": ["leisure=park"], "playground": ["leisure=playground"], "botanical_garden": ["leisure=garden"],
    "college_university": ["amenity=university"], "school": ["amenity=school"], "elementary_school": ["amenity=school"], "high_school": ["amenity=school"], "middle_school": ["amenity=school"],
    "christian_place_of_worship": ["amenity=place_of_worship"], "roman_catholic_place_of_worship": ["amenity=place_of_worship"], "protestant_place_of_worship": ["amenity=place_of_worship"],
    # le corrispondenze CHIARE che mancavano (30 set 2026: confronto con le categorie vere di sei
    # grandi città — Roma, Milano, Parigi, Tokyo, New York, Bangkok): l'app cerca questi tag e
    # Overture li aveva, ma nessuna riga li traduceva
    "dialysis_clinic": ["healthcare=dialysis", "amenity=clinic"], "currency_exchange": ["amenity=bureau_de_change"],
    "stadium_arena": ["leisure=stadium"], "football_stadium": ["leisure=stadium"], "baseball_stadium": ["leisure=stadium"],
    "basketball_stadium": ["leisure=stadium"], "monument": ["historic=monument"], "sculpture_statue": ["tourism=artwork"],
    "beach": ["natural=beach"], "rock_climbing_spot": ["leisure=climbing"], "climbing_gym": ["leisure=climbing"],
    "tutoring_service": ["amenity=prep_school"], "test_preparation": ["amenity=prep_school"],
    "social_and_human_service": ["amenity=social_facility"], "homeless_shelter": ["amenity=social_facility"],
    "social_or_community_service": ["amenity=social_facility"],
    "recycling_center": ["amenity=recycling"], "internet_cafe": ["amenity=internet_cafe"], "cultural_center": ["amenity=community_centre"], "community_center": ["amenity=community_centre"],
}

# quando `taxonomy.primary` manca, la categoria larga — solo quelle che dicono il mestiere
BASIC_A_OSM: dict[str, list[str]] = {
    "pharmacy_and_drug_store": ["amenity=pharmacy"], "gas_station": ["amenity=fuel"], "dental_clinic": ["amenity=dentist", "healthcare=dentist"],
    "attorney_or_law_firm": ["office=lawyer"], "restaurant": [R], "bar": ["amenity=bar"], "cafe": ["amenity=cafe"],
}


def tag_di(tax, bc):
    """I tag OSM di un posto di Overture. Una RETE DI SICUREZZA per i ristoranti:
    una cucina che la tabella non conosce ancora («georgian_restaurant») resta
    almeno un ristorante — mai più un posto che sparisce perché la sua cucina
    manca (il «Panda» coreano, 28 set 2026)."""
    if tax in TAX_A_OSM:
        return TAX_A_OSM[tax]
    if tax and tax.endswith("_restaurant"):
        return [R]
    if not tax:
        return BASIC_A_OSM.get(bc)
    return None
