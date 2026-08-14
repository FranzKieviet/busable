def get_place_query(xMin, xMax, yMin, yMax):
    return f"""
                SELECT 
                    id,
                    names.primary AS name,
                    categories.primary AS category,
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

                FROM read_parquet('s3://overturemaps-us-west-2/release/2026-07-22.0/theme=places/type=place/*', hive_partitioning=1)

                WHERE bbox.xmin BETWEEN {xMin} AND {xMax}
                AND bbox.ymin BETWEEN {yMin} AND {yMax}
                AND confidence > 0.6
                AND category IN (
                -- Food, Coffee & Drink
                'african_restaurant', 'american_restaurant', 'asian_fusion_restaurant', 'asian_restaurant',
                'bagel_restaurant', 'bagel_shop', 'bakery', 'bar', 'bar_and_grill_restaurant', 'barbecue_restaurant',
                'beer_bar', 'beer_garden', 'bistro', 'brazilian_restaurant', 'breakfast_and_brunch_restaurant',
                'brewery', 'bubble_tea', 'buffet_restaurant', 'burger_restaurant', 'cafe', 'cafeteria',
                'cajun_and_creole_restaurant', 'chicken_restaurant', 'chicken_wings_restaurant', 'chinese_restaurant',
                'cocktail_bar', 'coffee_shop', 'comfort_food_restaurant', 'cupcake_shop', 'delicatessen',
                'desserts', 'dim_sum_restaurant', 'diner', 'donuts', 'ethiopian_restaurant', 'falafel_restaurant',
                'fast_food_restaurant', 'fondue_restaurant', 'french_restaurant', 'frozen_yoghurt_shop', 'gastropub',
                'gelato', 'greek_restaurant', 'halal_restaurant', 'himalayan_nepalese_restaurant', 'hot_dog_restaurant',
                'ice_cream_shop', 'indian_restaurant', 'italian_restaurant', 'japanese_restaurant', 'korean_restaurant',
                'mediterranean_restaurant', 'mexican_restaurant', 'middle_eastern_restaurant', 'milk_bar',
                'noodles_restaurant', 'pakistani_restaurant', 'pan_asian_restaurant', 'pancake_house',
                'persian_iranian_restaurant', 'pizza_restaurant', 'poke_restaurant', 'pub', 'salad_bar',
                'sandwich_shop', 'seafood_restaurant', 'smoothie_juice_bar', 'soup_restaurant', 'sports_bar',
                'sushi_restaurant', 'taco_restaurant', 'tapas_bar', 'tea_room', 'thai_restaurant', 'turkish_restaurant',
                'vegan_restaurant', 'vegetarian_restaurant', 'vietnamese_restaurant',

                -- Arts, Culture & Entertainment
                'art_gallery', 'art_museum', 'arts_and_entertainment', 'cinema', 'comedy_club',
                'cultural_center', 'dance_club', 'escape_rooms', 'karaoke', 'landmark_and_historical_building',
                'lounge', 'monument', 'museum', 'music_venue', 'performing_arts', 'science_museum',
                'sports_and_recreation_venue', 'stadium_arena', 'theatre', 'topic_concert_venue',

                -- Parks, Leisure & Outdoors
                'attractions_and_activities', 'dog_park', 'hiking_trail', 'national_park', 'park',
                'public_plaza', 'rock_climbing_gym', 'rock_climbing_spot', 'swimming_pool', 'tourist_attraction',

                -- Retail & Shopping
                'academic_bookstore', 'antique_store', 'art_supply_store', 'bookstore', 'boutique',
                'comic_books_store', 'convenience_store', 'department_store', 'discount_store',
                'farmers_market', 'gift_shop', 'grocery_store', 'hobby_shop', 'music_and_dvd_store',
                'shopping_center', 'supermarket', 'thrift_store', 'used_bookstore', 'used_vintage_and_consignment',

                -- Civic, Campus & Public Services
                'campus_building', 'college_university', 'community_center', 'library', 'post_office',
                'student_union', 'visitor_center'
                )
                ORDER BY popularity_score DESC;
            """