## Архитектура нашего проект - Телеграм бот, развернутый на сервере
#### Выбор архитектуры:
Наши исследования начались с выбора платформы на которой можно было бы разместить гороскоп. Основную конкуренцию между собой составили: веб-сайт, telegram bot и приложение для PC/Android/IOS. У каждой из платформ есть свои плюсы и минусы:

#### Веб сайт:
-  Сложен в реализации. Разработка и поддержка веб-сайта требуют значительных усилий, особенно если речь идет о создании отзывчивого дизайна и обеспечении безопасности данных.
-  Нуждается в раскрутке. Инвестирования в SEO и маркетинг, может сильно сказаться на бюджете команды. 

#### PC/Android/IOS
-  Сложно реализовать.
-  Другие люди не смогут получить доступ к приложению из официальных источников. Без лицензии на распространение приложения через официальные магазины (App Store, Google Play), доступ к нему будет ограничен, что может снизить его популярность.
-  Дизайн. Нам придется самостоятельно создавать дизайн приложения.  

#### Telegram bot:
-  Прост в реализации. Создать бота значительно проще благодаря доступным инструментам и библиотекам.
-  У Telegram есть свое community, поэтому раскрутить бота гораздо легче. Можно использовать сообщества и чаты для привлечения пользователей, что существенно упрощает процесс распространения.
-  Не нужно изобретать дизайн и морочиться с оформлением. Telegram уже предоставляет весь необходимый визуальный функционал, что позволяет сосредоточиться на функциональности и удобстве использования
-  Удобство использования и отсутствие большой конкуренции на рынке telegram ботов по астрологии
-  Простая реализация рассылки для популяризации продукта