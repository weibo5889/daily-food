'''
Author: weijay
Date: 2023-04-24 23:09:47
LastEditors: weijay
LastEditTime: 2023-04-25 00:09:13
Description: DataBase ORM 模型單元測試
'''

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.model import Restaurant, Base


class InitialDataBaseTest(unittest.TestCase):
    """建立測試資料庫環境"""

    SQLALCHEMY_DATABASE_URL = "sqlite:///"

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            cls.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.clear_compiled_cache()
        cls.engine.dispose()


class TestRestaurantModel(InitialDataBaseTest):
    def setUp(self) -> None:
        self.db = self.SessionLocal()

        self.fake_restaurant = Restaurant(
            name="測試1",
            address="台北市信義區松壽路6段",
            lat=25.03586,
            lng=121.56433,
            phone="02-1284193212",
        )

        self.db.add(self.fake_restaurant)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.delete(self.fake_restaurant)
        self.db.commit()
        self.db.close()

    def test_create_restaurant(self):
        restaurant = Restaurant(
            name="測試2",
            address="新北市汐止區大同路一段",
            lat=25.05741,
            lng=121.63418,
        )
        self.db.add(restaurant)
        self.db.commit()
        self.assertIsNotNone(restaurant.id)
        self.assertEqual(restaurant.name, "測試2")
        self.assertEqual(restaurant.address, "新北市汐止區大同路一段")
        self.assertEqual(restaurant.lat, 25.05741)
        self.assertEqual(restaurant.lng, 121.63418)
        self.assertEqual(restaurant.phone, None)
        self.assertEqual(restaurant.is_enable, 1)
        self.assertTrue(isinstance(restaurant.create_at, datetime))

    def test_read_restaurant(self):
        restaurant = self.db.query(Restaurant).filter(Restaurant.name == "測試1").first()

        self.assertIsNotNone(restaurant)
        self.assertEqual(restaurant.name, "測試1")
        self.assertEqual(restaurant.address, "台北市信義區松壽路6段")
        self.assertEqual(restaurant.lat, 25.03586)
        self.assertEqual(restaurant.lng, 121.56433)
        self.assertEqual(restaurant.phone, "02-1284193212")
        self.assertEqual(restaurant.is_enable, 1)
        self.assertTrue(isinstance(restaurant.create_at, datetime))
        self.assertEqual(restaurant.update_at, None)

    def test_update_restaurant(self):
        restaurant = Restaurant(name="測試3", address="test", lat=25.00000, lng=120.00000)

        self.db.add(restaurant)
        self.db.commit()

        restaurant = self.db.query(Restaurant).filter(Restaurant.name == "測試3").first()

        self.assertEqual(restaurant.address, "test")
        self.assertEqual(restaurant.update_at, None)

        restaurant.address = "update_test"
        restaurant.update_at = datetime.utcnow()

        self.db.commit()

        restaurant = self.db.query(Restaurant).filter(Restaurant.name == "測試3").first()

        self.assertEqual(restaurant.address, "update_test")
        self.assertTrue(isinstance(restaurant.update_at, datetime))

    def test_delete_restaurant(self):
        restaurant = Restaurant(name="測試4", address="test", lat=23.00000, lng=120.00000)

        self.db.add(restaurant)
        self.db.commit()

        restaurant = self.db.query(Restaurant).filter(Restaurant.name == "測試4").first()

        self.assertIsNotNone(restaurant)

        self.db.delete(restaurant)
        self.db.commit()

        restaurant = self.db.query(Restaurant).filter(Restaurant.name == "測試4").first()

        self.assertIsNone(restaurant)
