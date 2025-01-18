# `seller.py`

Этот скрипт создан для автоматического обновления цен и остатков товаров в магазине на платформе Ozon. Он берёт информацию об остатках и ценах из предоставленного файла и синхронизирует её с платформой.

## Основной функционал

1. ### Загрузка остатков
   - Скачивает файл с информацией об остатках товаров.
   - Обрабатывает эти данные и сопоставляет их с товарами в магазине Ozon.

2. ### Обновление остатков:
   - Автоматически обновляет количество доступных товаров на платформе Ozon.
   - Уведомляет **Ozon**, если какой-либо товар закончился
3. ### Обновление цен:
   - Передаёт актуальные цены из файла в магазин **Ozon**.
   - Обеспечивает соответствие цен между локальной системой и платформой.

## Требования
- **API-доступ к Ozon:** необходимо указать `Client ID` и `API Key`, чтобы скрипт мог взаимодействовать с API.
- **Файл с остатками и ценами:** перед запуском скрипта убедитесь, что в Excel-файле указаны актуальные данные.

# `market.py`
## Описание скрипта

Этот скрипт предназначен для автоматизации работы интернет-магазина с платформой **Яндекс.Маркет**. 
Он выполняет несколько ключевых задач, которые помогают поддерживать актуальность информации о товарах на маркетплейсе.

## Основной функционал

1. ### Синхронизация остатков товаров
   - Проверяет, соответствуют ли данные о наличии товаров на складе и на платформе **Яндекс.Маркет**.
   - Обновляет остатки, если обнаружены изменения.
2. ### Обновление цен

   - Скрипт проверяет актуальные цены, заданные продавцом, и обновляет их на **Яндекс.Маркете**. 
Таким образом, информация о стоимости товаров всегда соответствует действительности.

3. ### Поддержка моделей работы
Поддерживает такие модели работы, как:
 - **FBS** (Fulfillment by Seller) – хранение товаров на складе продавца.
 - **DBS** (Delivery by Seller) – доставка товаров осуществляется продавцом.
Скрипт обновляет остатки и цены для обеих моделей.

## Требования
- API-доступ к Яндекс.Маркету: укажите параметры доступа в конфигурации скрипта.
- Локальные данные о товарах: остатки и цены должны быть актуальными перед запуском.
