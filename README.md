# Dictionary

# Paraschos
- <strike>Django/Flask framework</strike>
- <strike>Login Screen</strike>
- <strike>Registration Screen</strike>
- <strike>Search Results Screen  (meaning, example sentences, synonyms, antonyms, translation)</strike>

# Prokopis
- Django/Flask framework
- User backend

# Frontend
- <strike>Login Screen</strike>
- <strike>Registration Screen</strike>
- Dashboard Screen (Word of the day, search bar, most searched words, games)
- <strike>Search Results Screen  (meaning, example sentences, synonyms, antonyms, translation)</strike>
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
