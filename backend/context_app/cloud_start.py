"""Container entry point with optional, one-time private administrator setup."""
import os
import uvicorn
from database.connection import init_db
from .cloud_bootstrap import bootstrap


if __name__ == '__main__':
    init_db()
    bootstrap()
    uvicorn.run('main:app', host='0.0.0.0', port=int(os.getenv('PORT', '8000')), workers=1)
