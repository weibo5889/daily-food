'''
Author: weijay
Date: 2023-04-24 15:56:51
LastEditors: weijay
LastEditTime: 2023-04-25 22:05:43
Description: server 主程式
'''

from app import create_app
from app.routers import register_router
from app.database import engine
from app import model

model.Base.metadata.create_all(bind=engine)

app = create_app("dev")

root_prefix = f"/api/{app.api_version}"

register_router(app, root_prefix)
