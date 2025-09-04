# 🕷️ Парсер каталога alkoteka.com

Простой и гибкий Scrapy-спайдер для парсинга товаров с сайта [alkoteka.com](https://alkoteka.com) через API.

Собирает данные о товарах: название, цена, объём, ссылка, наличие, описание и другую информацию. Поддерживает:
- 🔍 Парсинг через API
- 🔄 Динамическую пагинацию (автоопределение последней страницы по `meta.has_more_pages`)
- 📁 Загрузку категорий из внешнего файла
- 🧩 Гибкую конфигурацию: можно запускать с файлом или без
- 📤 Экспорт в JSON (поддержка других форматов — возможно добавить)

---

## 📦 Установка
1. TOTAL COMMANDS:
    ```bash
   python --version
   git clone https://github.com/MrEnglishCat/scrrappy.git
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   cd alkoteka
   scrapy crawl alkoteka -O result.json

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
3. Есть 2 команды для запуска:
    - С указанием абсолютного пути к файлу с исходными ссылками на категории:
        ```bash 
        scrapy crawl alkoteka -a file_path=D:\_work\tests\scrrappy\test.txt -O result.json 
   
    - Без указания пути к файлу с ссылками на категории(в этом случае в коде должен быть заполнен атрибут STARTS_URL класса Alkoteka либо в виде списка, либо кортежа! НЕ ИСПОЛЬЗОВАТЬ ИТЕРАТОР!)
    
        ```bash
        scrapy crawl alkoteka -O result.json
   

