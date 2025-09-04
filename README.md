# 🕷️ Парсер каталога alkoteka.com

Простой и гибкий Scrapy-спайдер для парсинга товаров с сайта [alkoteka.com](https://alkoteka.com) через API.

Собирает данные о товарах: название, цена, объём, ссылка, наличие, описание и другую информацию. Поддерживает:
- 🔍 Парсинг через API
- 🔄 Динамическую пагинацию (автоопределение последней страницы по `meta.has_more_pages`)
- 📁 Загрузку категорий из внешнего файла
- 🧩 Гибкую конфигурацию: можно запускать с файлом или без
- 🧩 Гибкую конфигурацию: так же можно вводить нужное название города. 
- 📤 Экспорт в JSON (поддержка других форматов — возможно добавить)

---

## 📦 Установка

1. Убедитесь, что установлен **Python 3.12 или выше**  
   Проверить:  
   ```bash
   python --version

1. Клонировать проект: 
    ```bash
    git clone https://github.com/MrEnglishCat/scrrappy.git
    ```
1. Создать виртуальное окружение: 
    ```bash
    python -m venv venv

2. Активировать виртуальное окружение: 
     - Windows:
        ```bash
        venv\Scripts\activate
     - Linux/macOS:
        ```bash
       source venv/bin/activate
        
3. Установить пакеты из requirements.txt
     ```bash
    pip install -r requirements.txt
   
1. Перейти в каталог cd alkoteka (внутри должен остаться еще один каталог alkoteka)

    ```bash
    cd alkoteka
3. Есть 3 команды для запуска:
    - С указанием абсолютного(или относительного - к "/scrrappy/alkoteka") пути к файлу с исходными ссылками на категории:
        ```bash 
        scrapy crawl alkoteka -a file_path=D:\_work\tests\scrrappy\test.txt -O result.json 
   
    - Без указания пути к файлу с ссылками на категории(в этом случае в коде должен быть заполнен атрибут STARTS_URL класса Alkoteka либо в виде списка, либо кортежа! НЕ ИСПОЛЬЗОВАТЬ ИТЕРАТОР!)
    
        ```bash
        scrapy crawl alkoteka -O result.json
    - С указанием локации для поиска:
        ```bash
        # Пример команды с параметром для изменения локации!
        scrapy crawl alkoteka -a city_name=<Название города, не менее 3х символов> -O result.json
   
    Параметр city_name & file_path можно комбинировать.

### 📦 УСТАНОВКА И ЗАПУСК ЧЕРЕЗ ТЕРМИНАЛ

1. Нужен предустановленный **python 3.12+**
    ```bash
    python --version
    git clone https://github.com/MrEnglishCat/scrrappy.git
    cd scrrappy
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    cd alkoteka
   
    # команда запуска без файла со списком URL
    scrapy crawl alkoteka -O result.json
   
    # команда запуска с указанием абсолютного пути файла с URL
    scrapy crawl alkoteka -a file_path=D:\_work\tests\scrrappy\test.txt -O result.json
   
    # или относительного пути, относительно каталого scrrappy/alkoteka (из него запускается парсер)
    scrapy crawl alkoteka -a file_path=..\test.txt -O result.json
   
    # Пример команды с параметром для изменения локации!
    scrapy crawl alkoteka -a city_name=<Название города, не менее 3х символов> -O result.json