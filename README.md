# realty-service

### Эндпоинты API сервиса

#### 1. /registration [POST] - Регистрация пользователя
Регистрация пользователя в радиусе объекта (100 м.), после регистрации отправляет письмо об успешной регистрации,
на указанный при регистрации email. 


##### Параметры запроса:
В *body* запроса передается объект модели **UserIn**.

##### Ответ сервера:
Сервер возвращает объект модели **UserOut**

#### 2. /login [POST] - Авторизация пользователя 
При успешной авторизации возрващает jwt-token.

##### Параметры запроса:
В *body* запроса передается объект модели **UserIn**.

##### Ответ сервера:
Сервер возвращает объект модели **Token**


#### 3. /requests [POST] - Создать запрос 
Создать новый запрос может только пользователь.

##### Параметры запроса:
В *body* запроса передается объект модели **RequestIn**.\
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает объект модели **RequestOut**
    
#### 4. /requests [GET] - Получить список запрос 
**Пользователь** получает список свох запросов.\
**Сотрудник** получает список запросов назначенных на него.\
**Администратор объекта** получает список всех запросов по его объекту.\
**Админ** получает список всех запросов кроме тех что в статусе черновика.

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает список объектов модели:
- **RequestOut** для пользователей
- **RequestOutEmployee** для сотрудников
- **RequestOutAdmin** для администратора / админа

#### 5. /requests/{request_id} [GET] - Получить запрос по id 

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает объект модели:
- **RequestOut** для пользователей
- **RequestOutEmployee** для сотрудников
- **RequestOutAdmin** для администратора / админа

	
#### 6. /requests/{request_id} [PATCH] - Изменить данные запроса
Обновляет такие поля запроса как *title* и *description*
	
##### Параметры запроса:
В *body* запроса передается объект модели **RequestIn**.\
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
ервер возвращает объект модели:
- **RequestOut** для пользователей
- **RequestOutEmployee** для сотрудников
- **RequestOutAdmin** для администратора / админа

#### 7. /requests/status/{request_id} [PATCH] - Изменить статус запроса
**Пользователь** может изменить статус с *draft* на *active*.\
**Сотрудник / Администратор объекта / Админ** может изменить с *active* на *in_progress*, с *in_progress* на *finished*.
	
##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает список объектов модели:
- **RequestOut** для пользователей
- **RequestOutEmployee** для сотрудников
- **RequestOutAdmin** для администратора / админа

#### 8. /employee [POST] - Создать сотрудника 
Создать нового сотрудника может только **Администратор объекта**. Сотрудник автоматически привязывается к *объекту
администратора*. После регистрации сотруднику отправляется письмо об успешной регистрации.

##### Параметры запроса:
В *body* запроса передается объект модели **UserIn**.\
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает объект модели **UserOut**

#### 9. /employee [GET] - Получить список сотрудников 
Каждый **Администратор объекта** получает список своих сотрудников.

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает список объектов модели **UserOut**

#### 10. /employee/assign [PATCH] - Назначить сотрудника на запрос 
Каждый **Администратор объекта** может назначить только своего сотрудника на запрос относящийся к его объекту.

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации.\
В *path* запроса передаются параметры: **employee_id** и **request_id**

##### Ответ сервера:
Сервер возвращает объект модели **RequestOutAdmin**


#### 11. /admin [POST] - Создать администратора объетка
Создание **Администратора** и привязка его к объекту. После регистрации администратору отправляется письмо об успешной
регистрации.

##### Параметры запроса:
В *body* запроса передается объект модели **UserIn**.\
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает объект модели **UserOut**

#### 12. /admin/users [GET] - Получение списка всех пользователей системы 
Получение списка всех пользователей системы с возможностью фильтровать по ролям и объектам.

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации.\
В *path* запроса могут как присутствовать, так и отсутсвовать параметры фильтра: **role** и **building_id**

##### Ответ сервера:
Сервер возвращает список объект модели **UserOut**

#### 13. /admin/building [POST] - Создать бизнес-центр 
Создание нового объекта.

##### Параметры запроса:
В *body* запроса передается объект модели **BuildingIn**.\
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает объект модели **BuildingOut**

#### 14. /admin/building [GET] - Получить список всех бизнес-центров
Получить список с детальной информацией о каждом бизнес-центре

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает список объектов модели **BuildingOut**

#### 15. /admin/building/{building_id} [GET] - Получить данные бизне-центра 
Получить детальную информацию о бизнес-центре

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации 

##### Ответ сервера:
Сервер возвращает объект модели **BuildingOut**

#### 16. /admin/building/{building_id} [PATCH] - Изменить данные бизнес-центра
**Админ** может обновить информацию о бизнес-центре.

##### Параметры запроса:
В *header* запроса передается параметр **jwt** с данными токена полученного при авторизации.\
В *path* запроса: 
- building_id - id объекта (обязательное поле)
- name - новое имя объекта (необязательное поле)
- description - новое описание объекта (необязательное поле)
- square - новая площадь объекта (необязательное поле)

##### Ответ сервера:
Сервер возвращает объект модели **BuildingOut**


### Модели входящих и исходящих данных API


##### UserIn:

    {
        email*: string($email)
        title: Email
        The email a user
        
        password*: string
        title: Password
        minLength: 4
        The password a user
        
        building_id: string
        title: Building Id
        The object that the user belongs to

    }

##### UserOut:

    {
        user_id: string
        title: User Id
        The id a user
        
        building_id: string
        title: Building Id
        The object that the user belongs to
        
        email: string($email)
        title: Email
        The email a user
        
        role: string
        title: Role
        The role a user in app
        
        date_registration: string
        title: Date Registration
        Date of user registration in the system
    }


##### Token:
    {
        access_token*: string
        title: Access Token
        
        token_type*: string
        title: Token Type
    }


##### RequestIn:
    {
        title*: string
        title: Title
        minLength: 2
        The title of a request
        
        description*: string
        title: Description
        minLength: 5
        The description of a request
        
        date_receipt*: string($date-time)
        title: Date Receipt
        Date and time the request was created
    }

##### RequestOut:
    {
        request_id: string
        title: Request Id
        
        title: string
        title: Title
        minLength: 2
        The title of a request
        
        description: string
        title: Description
        minLength: 10
        The description of a request
        
        status: string
        title: Status
        minLength: 4
        default: draft
        The status of a request
        
        date_receipt: string($date-time)
        title: Date Receipt
        Date and time the request was created
    }

##### RequestOutEmployee:
    {
        request_id: string
        title: Request Id
        
        title: string
        title: Title
        minLength: 2
        The title of a request
        
        description: string
        title: Description
        minLength: 10
        The description of a request
        
        status: string
        title: Status
        minLength: 4
        default: draft
        The status of a request
        
        date_receipt: string($date-time)
        title: Date Receipt
        Date and time the request was created
        
        user_id: string
        title: User Id
    }


##### RequestOutAdmin:
    {
        request_id: string
        title: Request Id
        
        title: string
        title: Title
        minLength: 2
        The title of a request
        
        description: string
        title: Description
        minLength: 10
        The description of a request
        
        status: string
        title: Status
        minLength: 4
        default: draft
        The status of a request
        
        date_receipt: string($date-time)
        title: Date Receipt
        Date and time the request was created
        
        user_id: string
        title: User Id
        
        employee_id: string
        title: Employee Id
        
        building_id: string
        title: Building Id
    }


##### BuildingIn:
    {
        location*: tuple(lat, lon)
        title: Location
        The coordinates of the location

        name*: string
        title: Name
        The name of the building
        
        description*: string
        title: Description
        Building description
        
        square*: float
        title: Square
        Square area of the building
    }
    
##### BuildingOut:
    {
        building_id: string
        title: Building Id
        The object that the user belongs to
        
        location: tuple(lat, lon)
        title: Location
        The coordinates of the location
        
        name: string
        title: Name
        The name of the building
        
        description: string
        title: Description
        Building description
        
        square: float
        title: Square
        Square area of the building
    }


### Модели данных MongoDB

##### Users
- _id: ObjectId
- building_id: str
- email: EmailStr
- hash_password: str
- role: str
- date_registration: datetime

##### Requests
- _id: ObjectId
- user_id: str
- employee_id: str
- building_id: str
- title: str
- description: str
- status: str
- date_receipt: datetime

##### Buildings
- _id: ObjectId
- location: tuple('lat', 'lon')
- name: str
- description: str
- square: float