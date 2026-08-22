SELECT
    id,
    c_description,
    c_language_code,
    c_polygon
FROM t_place
WHERE id IN ({})