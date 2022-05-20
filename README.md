# Dictionary

# Dimitris
- Django/Flask framework
- Login/Registration Screen

# Paraschos
- Django/Flask framework
- Design (Wireframe)

# Prokopis
- Django/Flask framework
- User backend

# Frontend
- Login Screen
- Registration Screen
- Dashboard Screen (Word of the day, search bar, most searched words, games)
- Search Results Screen  (meaning, example sentences, synonyms, antonyms, translation)
- Menu (User Settings, Favorites, Word history, logout)

# Backend
- Generate dictionary data (APIs)
- PostgreSQL -> User Table (id, firstName, lastName, email, username, password, List[SearchResult] favorites, List[SearchResult] searchResults )
- SQLite ->  User Table (id, firstName, lastName, email, username, password, List[SearchResult] favorites, List[SearchResult] searchResults )

# API routes:
- /login (username, password) || (email, password)
- /register (User)
- /searchResult (searchResult)
- /history (userId)
- /favorites (userId)
