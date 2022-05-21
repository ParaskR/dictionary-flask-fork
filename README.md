# Dictionary

# Paraschos
- <strike>Django/Flask framework</strike>
- <strike>Login Screen</strike>
- <strike>Registration Screen</strike>
- <strike>Search Results Screen  (meaning, example sentences, synonyms, antonyms, translation)</strike>
- <strike>Generate dictionary data (APIs)</strike>
- Menu (User Settings, Favorites, Word history, logout)
- Dashboard Screen (Word of the day, search bar, most searched words, games)


# Prokopis
- Django/Flask framework
- User backend

# Frontend
- <strike>Login Screen</strike>
- <strike>Registration Screen</strike>
- <strike>Search Results Screen  (meaning, example sentences, synonyms, antonyms, translation)</strike>
- Dashboard Screen (Word of the day, search bar, most searched words, games)
- Menu (User Settings, Favorites, Word history, logout)
- User/Account Screen

# Backend
- <strike>Generate dictionary data (APIs)</strike>
- PostgreSQL -> User Table (id, firstName, lastName, email, username, password, List[SearchResult] favorites, List[SearchResult] searchResults )
- SQLite ->  User Table (id, firstName, lastName, email, username, password, List[SearchResult] favorites, List[SearchResult] searchResults )

# API routes:
- /login (username, password) || (email, password)
- /register (User)
- /searchResult (searchResult)
- /history (userId)
- /favorites (userId)
