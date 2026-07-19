import os
from app import create_app

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    print("="*40)
    print(" SupplyShield v0.1.0")
    print(f" Running in '{config_name}' mode")
    print("="*40)
    app.run(host='0.0.0.0', port=5000)
