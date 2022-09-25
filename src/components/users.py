import hashlib
import secrets

from src.utils.db_tools import check_session_key
from src.utils.db_utils import connect


def rebuild_users_table():
    """
    This function will empty the users table
    """
    conn = connect()
    cur = conn.cursor()
    drop_sql = """
        DROP TABLE if EXISTS users CASCADE;
        """
    create_sql = """
        CREATE TABLE users(
            id              SERIAL PRIMARY KEY,
            username        TEXT NOT NULL,
            password        TEXT NOT NULL,
            profile_pic     bytea DEFAULT NULL,
            email           TEXT NOT NULL,
            session_key     TEXT
        )
        """
    cur.execute(drop_sql)
    cur.execute(create_sql)
    conn.commit()
    conn.close()


def create_user(username, password, email):
    """
    This function will create a new user
    :param username: The new user's username
    :param password: The new user's password
    :param email: the new user's email
    :return: a message based on the status
    """
    conn = connect()
    cur = conn.cursor()

    username_check = """
        SELECT COUNT(*) FROM users
        WHERE username = %s
        """
    cur.execute(username_check, [username])
    outcome = cur.fetchall()

    if len(outcome) > 0:
        conn.close()
        return "A user with that username already exists"

    encrypted = hashlib.sha512(password.encode()).hexdigest()

    add_user = """
        INSERT INTO users(username, password, email) VALUES
        (%s, %s, %s)
        RETURNING id
        """
    cur.execute(add_user, (username, encrypted, email))
    outcome = cur.fetchall()

    if outcome == ():
        conn.close()
        return "An error occurred, try again"

    conn.commit()
    conn.close()
    return "Success!"


def login_user(username, password):
    """
    This will log a user in and get them the session
    key for their current session
    :param username: the user's username
    :param password: the user's password
    :return: the session key of successful, error string if not
    """
    conn = connect()
    cur = conn.cursor()

    encrypted = hashlib.sha512(password.encode()).hexdigest()

    request = """
        SELECT session_key FROM users
        WHERE users.username = %s and users.password = %s
        """
    cur.execute(request, (username, encrypted))
    outcome = cur.fetchall()

    if not outcome:
        conn.close()
        return "Bad username or password"

    if outcome[0] == (None,):
        session_key = secrets.token_hex(16)
        session_key_request = """
            UPDATE users
            SET session_key = %s
            WHERE users.username = %s and users.password = %s
            """
        cur.execute(session_key_request, (session_key, username, encrypted))

        conn.commit()
        conn.close()
        return session_key


def logout_user(user_id, session_key):
    """
    This function will log a user out and wipe
    their session key from the database

    :param user_id: the user's id
    :param session_key: the user's current session_key

    :return: "signed out" if signed out, "bad request" otherwise
    """
    valid = check_session_key(user_id, session_key)

    if valid:
        conn = connect()
        cur = conn.cursor()
        request = """
            UPDATE users
            SET session_key = ''
            WHERE users.id = %s
            """
        cur.execute(request, [user_id])

        conn.commit()
        conn.close()

        return "signed out"
    return "bad request"
