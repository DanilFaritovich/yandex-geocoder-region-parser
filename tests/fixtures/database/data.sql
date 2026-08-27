INSERT INTO t_place (
    id,
    c_description,
    c_language_code,
    c_polygon_text
)
VALUES
    (
        1,
        'Yerevan',
        'hy',
        'POLYGON((44.50 40.15, 44.51 40.15,
                  44.51 40.16, 44.50 40.16,
                  44.50 40.15))'
    ),
    (
        2,
        'Dubai',
        'en',
        'POLYGON((55.27 25.20, 55.28 25.20,
                  55.28 25.21, 55.27 25.21,
                  55.27 25.20))'
    ),
    (
        3,
        'Moscow',
        'ru',
        'POLYGON((37.60 55.70, 37.61 55.70,
                  37.61 55.71, 37.60 55.71,
                  37.60 55.70))'
    );