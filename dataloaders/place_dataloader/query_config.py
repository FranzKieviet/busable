def get_place_query(release, xMin, xMax, yMin, yMax):
    return f"""
                SELECT 
                    id,
                    names.primary AS name,
                    taxonomy.primary AS category,
                    confidence,
                    brand.names.primary AS brand,
                    websites[1] AS website,
                    
                    -- Extract GeoJSON Geometry string
                    ST_AsGeoJSON(geometry) AS geojson_geometry,
                    
                    -- Heuristic Popularity Score
                    (
                        (confidence * 50) +
                        (CASE WHEN brand.names.primary[1] IS NOT NULL THEN 20 ELSE 0 END) +
                        (CASE WHEN websites[1] IS NOT NULL THEN 15 ELSE 0 END) +
                        (CASE WHEN len(socials) > 0 THEN 15 ELSE 0 END)
                    ) AS popularity_score

                FROM read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*', hive_partitioning=1)

                WHERE bbox.xmin BETWEEN {xMin} AND {xMax}
                AND bbox.ymin BETWEEN {yMin} AND {yMax}
                AND operating_status != 'permanently_closed'
                AND confidence > 0.6
                AND category IN (
                -- Food, Coffee & Drink
                'african_restaurant', 'american_restaurant', 'asian_fusion_restaurant', 'asian_restaurant',
                'bagel_shop', 'bakery', 'bar', 'bar_and_grill_restaurant', 'barbecue_restaurant',
                'beer_bar', 'beer_garden', 'bistro', 'brazilian_restaurant', 'breakfast_and_brunch_restaurant',
                'brewery', 'bubble_tea_shop', 'buffet_restaurant', 'burger_restaurant', 'cafe', 'cafeteria',
                'cajun_and_creole_restaurant', 'chicken_restaurant', 'chicken_wings_restaurant', 'chinese_restaurant',
                'cocktail_bar', 'coffee_shop', 'comfort_food_restaurant', 'cupcake_shop', 'delicatessen',
                'dessert_shop', 'dim_sum_restaurant', 'diner', 'donut_shop', 'ethiopian_restaurant', 'falafel_restaurant',
                'fast_food_restaurant', 'fondue_restaurant', 'french_restaurant', 'frozen_yogurt_shop', 'gastropub',
                'gelato_shop', 'greek_restaurant', 'halal_restaurant', 'nepalese_restaurant', 'hot_dog_restaurant',
                'ice_cream_shop', 'indian_restaurant', 'italian_restaurant', 'japanese_restaurant', 'korean_restaurant',
                'mediterranean_restaurant', 'mexican_restaurant', 'middle_eastern_restaurant', 'ramen_restaurant',
                'pakistani_restaurant', 'pan_asian_restaurant', 'pancake_house',
                'persian_restaurant', 'pizza_restaurant', 'poke_restaurant', 'pub', 'salad_bar',
                'sandwich_shop', 'seafood_restaurant', 'smoothie_juice_bar', 'soup_restaurant', 'sports_bar',
                'sushi_restaurant', 'taco_restaurant', 'tapas_bar', 'tea_room', 'thai_restaurant', 'turkish_restaurant',
                'vegan_restaurant', 'vegetarian_restaurant', 'vietnamese_restaurant',

                -- Arts, Culture & Entertainment
                'art_gallery', 'art_museum', 'arts_and_entertainment', 'movie_theater', 'comedy_club',
                'cultural_center', 'dance_club', 'escape_room', 'karaoke_venue', 'historic_site',
                'lounge', 'monument', 'museum', 'music_venue', 'performing_arts_venue', 'science_museum',
                'sport_or_fitness_facility', 'stadium_arena', 'theatre_venue',

                -- Parks, Leisure & Outdoors
                'dog_park', 'hiking_trail', 'national_park', 'park',
                'public_plaza', 'rock_climbing_gym', 'rock_climbing_spot', 'swimming_pool',

                -- Retail & Shopping
                'academic_bookstore', 'antique_store', 'art_supply_store', 'bookstore', 'fashion_boutique',
                'comic_books_store', 'convenience_store', 'department_store', 'discount_store',
                'farmers_market', 'gift_shop', 'grocery_store', 'hobby_shop', 'music_and_dvd_store',
                'shopping_mall', 'second_hand_store', 'used_bookstore', 'second_hand_clothing_store',

                -- Civic, Campus & Public Services
                'campus_building', 'college_university', 'community_center', 'library', 'post_office',
                'student_union', 'visitor_center'
                )
                ORDER BY popularity_score DESC;
            """