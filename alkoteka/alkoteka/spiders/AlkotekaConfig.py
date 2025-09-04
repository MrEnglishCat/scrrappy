from dataclasses import dataclass


@dataclass
class AlkotekaConfig:
    BASE_URL = 'https://alkoteka.com'

    # ALKOTEKA_API_CATALOG: str = 'https://alkoteka.com/web-api/v1/product?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&page={page}&per_page={per_page}&root_category_slug={root_category_slug}'
    ALKOTEKA_API_CATALOG: str = 'https://alkoteka.com/web-api/v1/product?city_uuid={current_city_uuid}&page={page}&per_page={per_page}&root_category_slug={root_category_slug}'
    """
    в meta "has_more_pages": false, - можно определить  последняя ли это страница
    Используется для получения списка слагов на товары. Лимиты выставляются передавая параметр per_page, page
    """

    # ALKOTEKA_API_ITEM_URL: str = 'https://alkoteka.com/web-api/v1/product/{item_slug}?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416'
    ALKOTEKA_API_ITEM_URL: str = 'https://alkoteka.com/web-api/v1/product/{item_slug}?city_uuid={current_city_uuid}'
    """
    API для получения данных об определенном товаре
    """

    # ALKOTEKA_API_CITY_SEARCH: str = 'https://alkoteka.com/web-api/v1/city?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&search={city_name}'
    ALKOTEKA_API_CITY_SEARCH: str = 'https://alkoteka.com/web-api/v1/city?city_uuid={current_city_uuid}&search={city_name}'
    """
    API для поиска города, передается в параметр search
    используется для получения определенного города    
    """

    ALKOTEKA_API_ALL_CITY: str = 'https://alkoteka.com/web-api/v1/city?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&page={page}'  # всего 3 страницы, 59 городов
    """
    Можно получить все доступные города, ответ по страницам. 
    
    НЕ ИСПОЛЬЗУЕТСЯ, НО ОНА ЕСТЬ
    """

    PROXY_FILEPATH: str = "proxy_pool.json"

    current_city_uuid: str = '4a70f9e0-46ae-11e7-83ff-00155d026416'
    """
    идентификатор Краснодара для API       
    """


    DEFAULT_PER_PAGE = 200