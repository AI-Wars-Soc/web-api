from gevent import monkey
monkey.patch_all()

from views import app
import cuwais.database

cuwais.database.create_tables()

if __name__ == "__main__":
    app.run()
