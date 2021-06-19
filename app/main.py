from gevent import monkey
monkey.patch_all()

from views import app
import cuwais.database

if __name__ == "__main__":
    cuwais.database.create_tables()
    app.run()
