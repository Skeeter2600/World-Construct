from src.utils.db_tools import check_session_key
from src.utils.db_utils import connect


def rebuild_npc_npc_linker():
    """
    This function will empty the npc npc linker table
    """
    conn = connect()
    cur = conn.cursor()
    drop_sql = """
        DROP TABLE if EXISTS npc_npc_linker CASCADE;
        """
    create_sql = """
        CREATE TABLE npc_npc_linker(
            id              SERIAL PRIMARY KEY,
            npc_1_id         INTEGER NOT NULL REFERENCES npcs ON DELETE CASCADE,
            npc_2_id         INTEGER NOT NULL REFERENCES npcs ON DELETE CASCADE
        )
        """
    cur.execute(drop_sql)
    cur.execute(create_sql)
    conn.commit()
    conn.close()


def add_npc_npc_association(npc1_id, npc2_id, user_id, session_key):
    """
    This function will add an association between
    a city and an npc to the linker table

    :param npc1_id: the id of the npc
    :param npc2_id: the id of the city
    :param user_id: the id of the user requesting this
    :param session_key: the user's session key

    :return: True if successful, False if not
    """
    if check_session_key(user_id, session_key):
        # TODO add logic
        return True
    return False


def get_associated_npcs(npc_id):
    """
    This function will get a list of npcs who
    are associated with the specified npc
    :param npc_id: the id of the npc being checked

    :return: a list with a dictionary of the values

    :format return: [{ id: npc id,
                       name: npc name}]
    """
    conn = connect()
    cur = conn.cursor()

    npc_list = []

    npc2_query = """
        SELECT npcs.id, name FROM npc_npc_linker
            INNER JOIN npcs ON npc_npc_linker.npc_2_id = npcs.id
        WHERE npc_1_id = %s
        """
    cur.execute(npc2_query, [npc_id])
    npc_list.extend(cur.fetchall())

    npc1_query = """
            SELECT npcs.id, name FROM npc_npc_linker
                INNER JOIN npcs ON npc_npc_linker.npc_1_id = npcs.id
            WHERE npc_2_id = %s
            """
    cur.execute(npc1_query, [npc_id])
    npc_list.extend(cur.fetchall())

    conn.close()
    return npc_list