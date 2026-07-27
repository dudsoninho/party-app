import os

class Config:
    SECRET_KEY = 'motylcoin-super-bezpieczny-klucz-sesji'
    # Wskazanie na bazę danych w głównym folderze
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
