import argparse
import uvicorn
from .api import create_app
from .storage import SQLiteStore

parser = argparse.ArgumentParser()
parser.add_argument('--db', default='crypto.sqlite3')
parser.add_argument('--port', type=int, default=8000)
args = parser.parse_args()
uvicorn.run(create_app(SQLiteStore(args.db)), host='127.0.0.1', port=args.port)
