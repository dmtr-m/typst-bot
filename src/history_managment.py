from collections import deque

class history:
    """
    Stores most recent queries of last MAX_USERS_NUMBER users.
    Data is stored in a dictionary the key is user_id.
    """
    def __init__(self, MAX_USERS_NUMBER = 100) -> None:
        self._MAX_USERS_NUMBER = MAX_USERS_NUMBER
        self._most_recent_users = deque()
        self._history_by_user = dict()
    
    def new_query(self, user: int, query: str) -> None:
        """
        Adds to the dict: user - key, query - value;
        Oldest query deleted if maximum number is exceeded.
        input: int (user id), str (query)
        """
        if user in self._history_by_user:
            self._history_by_user[user] = query
        else:
            self._most_recent_users.append(user)
            self._history_by_user[user] = query
            if len(self._most_recent_users) > self._MAX_USERS_NUMBER:
                user_to_delete = self._most_recent_users.popleft()
                self._history_by_user.pop(user_to_delete, None)

    def recent_query(self, user: int) -> str:
        """
        Returns the last query of the user (by id),
        if nothing stored, returns message.
        input: int (user id)
        output: str (users query or error message)
        """
        if user in self._history_by_user:
            return self._history_by_user[user]
        else:
            return 0
