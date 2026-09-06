from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
import os

# Подключение к базе данных PostgreSQL
DATABASE_URL = "postgresql://postgres:d7k_8TJsdt@localhost/postgres"

def execute_sql_from_file(file_path):
    """Выполняет SQL-команды из файла"""
    engine = create_engine(DATABASE_URL)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        sql_commands = file.read()
    
    with engine.connect() as conn:
        # Разбиваем команды на отдельные операторы
        # Обратите внимание, что в реальном приложении лучше использовать Alembic для миграций
        statements = sql_commands.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement:  # Пропускаем пустые строки
                try:
                    conn.execute(text(statement))
                    conn.commit()
                    print(f"Выполнена команда: {statement[:50]}...")
                except ProgrammingError as e:
                    print(f"Ошибка выполнения команды: {e}")
                    conn.rollback()
                except Exception as e:
                    print(f"Неизвестная ошибка: {e}")
                    conn.rollback()

def setup_database():
    """Создает структуру базы данных из файла struct.sql"""
    print("Начинаем настройку базы данных...")
    execute_sql_from_file('../migrations/struct.sql')
    print("Настройка базы данных завершена!")

if __name__ == "__main__":
    setup_database()