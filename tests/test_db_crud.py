'''
Author: weijay
Date: 2023-05-15 22:05:37
LastEditors: andy
LastEditTime: 2023-06-21 01:06:00
Description: DataBase CRUD 單元測試
'''

import os
import unittest
import datetime

from sqlalchemy import text

from app.schemas import database_schema
from app.database.model import Restaurant, RestaurantOpenTime, User
from app.database import crud
from tests.utils import FakeData, FakeDataBase


# TODO 這邊應該獨立出來
class InitialDataBaseTest(unittest.TestCase):
    """建立測試資料庫環境"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fake_database = FakeDataBase()
        cls.fake_database.Base.metadata.create_all(bind=cls.fake_database.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fake_database.engine.clear_compiled_cache()
        cls.fake_database.engine.dispose()
        cls.fake_database.Base.metadata.drop_all(bind=cls.fake_database.engine)
        os.remove("test.db")


class TestRestaurantCURD(InitialDataBaseTest):
    def _get_restaurant_obj(self, db) -> "Restaurant":
        r_obj = (
            db.query(Restaurant)
            .filter(Restaurant.name == self._fake_restaurant_data["name"])
            .first()
        )

        return r_obj

    def setUp(self) -> None:
        """先新增資料進去"""

        # TODO 這邊不要這樣，應該統一生成
        # NOTE 如果之後 Restaurant 有做更改的話，要檢查一下這邊
        self._fake_restaurant_data = {
            "name": "test_restaurant",
            "address": "test_address",
            "lat": 23.001,
            "lng": 120.001,
        }

        fake_restaurant = Restaurant(**self._fake_restaurant_data)

        with self.fake_database.get_db() as db:
            db.add(fake_restaurant)
            db.commit()

    def tearDown(self) -> None:
        with self.fake_database.get_db() as db:
            db.execute(text("DELETE FROM restaurant"))
            db.commit()

    def test_get_restaurants_function(self):
        with self.fake_database.get_db() as db:
            restaurants = crud.get_restaurants(db)

            fake_restaurant = self._get_restaurant_obj(db)

        self.assertTrue(isinstance(restaurants, list))
        self.assertEqual(restaurants[0].name, fake_restaurant.name)

    def test_create_restaurant_function(self):
        fake_data = FakeData.fake_restaurant()

        restaurant = database_schema.RestaurantDBModel(**fake_data)

        with self.fake_database.get_db() as db:
            db_restaurant = crud.create_restaurant(db, restaurant)

        self.assertIsNotNone(db_restaurant)
        self.assertTrue(isinstance(db_restaurant, Restaurant))
        self.assertEqual(db_restaurant.name, fake_data["name"])

    def test_update_restaurant_function(self):
        fake_data = FakeData.fake_restaurant()

        with self.fake_database.get_db() as db:
            db.add(Restaurant(**fake_data))
            db.commit()

        with self.fake_database.get_db() as db:
            restaurant = db.query(Restaurant).filter(Restaurant.name == fake_data["name"]).first()

            update_data = database_schema.RestaurantUpdateDBModel(name="測試2更新")

            updated_restaurant = crud.update_restaurant(db, restaurant.id, update_data)

        self.assertIsNotNone(updated_restaurant)
        self.assertEqual(updated_restaurant.name, "測試2更新")
        self.assertEqual(updated_restaurant.address, restaurant.address)
        self.assertEqual(updated_restaurant.phone, restaurant.phone)

    def test_update_restaurant_function_with_not_exist_id(self):
        fake_data = FakeData.fake_restaurant()

        update_data = database_schema.RestaurantDBModel(**fake_data)

        with self.fake_database.get_db() as db:
            upadted_restaurant = crud.update_restaurant(db, 1000, update_data)

        self.assertIsNone(upadted_restaurant)

    def test_delete_restaurant_function(self):
        fake_data = FakeData.fake_restaurant()

        with self.fake_database.get_db() as db:
            db.add(Restaurant(**fake_data))
            db.commit()

        with self.fake_database.get_db() as db:
            restaurant = db.query(Restaurant).filter(Restaurant.name == fake_data["name"]).first()

            crud.delete_restaurant(db, restaurant.id)

            deleted_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant.id).first()

        self.assertIsNotNone(restaurant)
        self.assertIsNone(deleted_restaurant)

    def test_delete_restaurant_function_with_not_eixst_id(self):
        with self.fake_database.get_db() as db:
            deleted_restaurant = crud.delete_restaurant(db, 1000)

        self.assertIsNone(deleted_restaurant)

    # TODO 這裡獨立出來
    def test_get_restaurant_randomly_function(self):
        fake_inner_data = FakeData.fake_restaurant()
        fake_outer_data = FakeData.fake_restaurant_far()

        inner_restaurant = Restaurant(**fake_inner_data)
        outer_restaurant = Restaurant(**fake_outer_data)

        with self.fake_database.get_db() as db:
            db.add_all([inner_restaurant, outer_restaurant])
            db.commit()

            inner_lat, inner_lng = FakeData.fake_current_location()
            random_restaurant = crud.get_restaurant_randomly(db, inner_lat, inner_lng, 5.0, 1)

        self.assertIsNotNone(random_restaurant)
        self.assertEqual(random_restaurant[0].name, fake_inner_data["name"])
        self.assertEqual(len(random_restaurant), 1)

    # TODO 這裡獨立出來
    def test_get_restaurant_randomly_with_open_time_function(self):
        fake_inner_data1, fake_inner_data2 = FakeData.fake_restaurant(number=2)

        inner_restaurant1 = Restaurant(**fake_inner_data1)
        inner_restauarnt2 = Restaurant(**fake_inner_data2)

        with self.fake_database.get_db() as db:
            db.add_all([inner_restaurant1, inner_restauarnt2])
            db.commit()
            db.refresh(inner_restaurant1)
            db.refresh(inner_restauarnt2)

        open_time1, open_time2 = FakeData.fake_restaurant_open_time(number=2)

        with self.fake_database.get_db() as db:
            db_open_time1 = RestaurantOpenTime(**open_time1)
            db_open_time2 = RestaurantOpenTime(**open_time2)

            inner_restaurant1.open_times.append(db_open_time1)
            inner_restauarnt2.open_times.append(db_open_time2)

            db.add_all([db_open_time1, db_open_time2])
            db.commit()

        with self.fake_database.get_db() as db:
            lat, lng = FakeData.fake_current_location()
            random_restaurant = crud.get_restaurant_randomly_with_open_time(
                db,
                lat,
                lng,
                5.0,
                open_time1["day_of_week"],
                open_time1["open_time"].strftime("%H:%M"),
                1,
            )

            self.assertEqual(len(random_restaurant), 1)
            self.assertEqual(len(random_restaurant[0].open_times), 1)
            self.assertEqual(
                random_restaurant[0].open_times[0].day_of_week, open_time1["day_of_week"]
            )
            self.assertEqual(random_restaurant[0].open_times[0].open_time, open_time1["open_time"])
            self.assertEqual(
                random_restaurant[0].open_times[0].close_time, open_time1["close_time"]
            )


class TestRestaurantOpenTimeCRUD(InitialDataBaseTest):
    def _get_restaurant_obj(self, db) -> "Restaurant":
        r_obj = db.query(Restaurant).filter(Restaurant.name == self.fake_data["name"]).first()

        return r_obj

    def _get_open_time_obj(self, db):
        open_time_obj = (
            db.query(RestaurantOpenTime)
            .filter(RestaurantOpenTime.day_of_week == self._fake_open_time_data["day_of_week"])
            .first()
        )

        return open_time_obj

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.fake_data = FakeData.fake_restaurant()

        with cls.fake_database.get_db() as db:
            restaurant = Restaurant(**cls.fake_data)

            db.add(restaurant)

            db.commit()
            db.refresh(restaurant)

    def setUp(self) -> None:
        """先新增資料"""

        # TODO 這邊不要這樣，應該統一生成
        self._fake_open_time_data = {
            "day_of_week": 100,
            "open_time": datetime.time(hour=8, minute=0),
            "close_time": datetime.time(hour=22, minute=0),
        }

        with self.fake_database.get_db() as db:
            r_obj = self._get_restaurant_obj(db)

            db_open_time = RestaurantOpenTime(**self._fake_open_time_data)

            r_obj.open_times.append(db_open_time)

            db.add(db_open_time)
            db.commit()

    def tearDown(self) -> None:
        with self.fake_database.get_db() as db:
            db.execute(text("DELETE FROM restaurant_open_time"))
            db.commit()

    def test_create_restaurant_open_time_function(self):
        fake_open_time = FakeData.fake_restaurant_open_time()

        with self.fake_database.get_db() as db:
            r_obj = self._get_restaurant_obj(db)

            crud.create_restaurant_open_times(
                db,
                r_obj.id,
                [
                    database_schema.RestaurantOpenTimeDBModel(**fake_open_time),
                ],
            )

            open_times = db.get(Restaurant, r_obj.id).open_times

            self.assertIn(fake_open_time["day_of_week"], [i.day_of_week for i in open_times])
            self.assertIn(fake_open_time["open_time"], [i.open_time for i in open_times])
            self.assertIn(fake_open_time["close_time"], [i.close_time for i in open_times])

    def test_update_restaurant_open_time_function(self):
        with self.fake_database.get_db() as db:
            open_time_obj = self._get_open_time_obj(db)

            self.assertEqual(open_time_obj.update_at, None)

            update_data = database_schema.RestaurantOpenTimeUpdateDBModel(
                day_of_week=5,
            )

            crud.update_restaurant_open_time(db, open_time_obj.id, update_data)

            updated_open_time = db.get(RestaurantOpenTime, open_time_obj.id)

            self.assertEqual(updated_open_time.day_of_week, 5)
            self.assertIsNotNone(updated_open_time.update_at)

    def test_delete_restaurant_open_time_function(self):
        with self.fake_database.get_db() as db:
            open_time = self._get_open_time_obj(db)

            crud.delete_restaurant_open_time(db, open_time.id)

            delete_open_time_obj = db.get(RestaurantOpenTime, open_time.id)

        self.assertIsNotNone(open_time)
        self.assertIsNone(delete_open_time_obj)


class TestUserCRUD(InitialDataBaseTest):
    def _get_user_obj(self, db) -> "User":
        user = db.query(User).filter(User.username == self._fake_user_data["username"]).first()

        return user

    def setUp(self) -> None:
        """先新增資料進去"""

        # TODO 這邊不要這樣，應該統一生成
        # NOTE 如果之後 User 有做更改的話要檢查一下這邊
        self._fake_user_data = {"username": "test", "email": "test@test.com", "password": "test"}

        fake_user = User(**self._fake_user_data)

        with self.fake_database.get_db() as db:
            db.add(fake_user)
            db.commit()

    def tearDown(self) -> None:
        """清理資料"""

        with self.fake_database.get_db() as db:
            db.execute(text("DELETE FROM user"))
            db.commit()

    def test_get_user_function(self):
        """測試取得 user"""

        with self.fake_database.get_db() as db:
            user = crud.get_user_not_oauth(db, self._fake_user_data["username"])

            fake_user = self._get_user_obj(db)

            self.assertEqual(user, fake_user)

    def test_create_user_function(self):
        """測試新增 user"""

        fake_user_date = FakeData.fake_user()

        with self.fake_database.get_db() as db:
            crud.create_user_not_oauth(
                db,
                database_schema.UserNotOAuthDBModel(
                    username=fake_user_date["username"],
                    email=fake_user_date["email"],
                    password=fake_user_date["password_hash"],
                ),
            )

            user = db.query(User).filter(User.username == fake_user_date["username"]).first()

            self.assertIsNotNone(user)
