from src.utils.db_tools import check_session_key
from src.utils.db_utils import connect
from src.utils.permissions import check_editable, check_viewable


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


def check_same_world(npc_1_id, npc_2_id):
    """
    This function will check if two elements are in
    the same world, which would allow a link

    :param npc_1_id: the id of the first npc
    :param npc_2_id: the id of the second npc

    :return: -1 if no link, the world id if they do
    """
    conn = connect()
    cur = conn.cursor()

    world_id_check = """
            SELECT world_id FROM npcs
            WHERE id = %s OR id = %s
        """
    cur.execute(world_id_check, [npc_1_id, npc_2_id])
    world_ids = cur.fetchall()
    conn.close()

    if world_ids[0][0] == world_ids[1][0]:
        return world_ids[0][0]

    return -1


def add_npc_npc_association(npc_1_id, npc_2_id, user_id, session_key):
    """
    This function will add an association between
    an npc and an npc to the linker table

    :param npc_1_id: the id of the first npc
    :param npc_2_id: the id of the second npc
    :param user_id: the id of the user requesting this
    :param session_key: the user's session key

    :return: True if successful, False if not
    """
    if check_session_key(user_id, session_key):
        world_id = check_same_world(npc_1_id, npc_2_id)

        if world_id > 0:
            if check_editable(world_id, user_id, session_key):
                conn = connect()
                cur = conn.cursor()

                insert_request = """
                    INSERT INTO npc_npc_linker(npc_1_id, npc_2_id) VALUES
                    (%s, %s)
                    RETURNING id
                    """
                cur.execute(insert_request, (npc_1_id, npc_2_id))
                outcome = cur.fetchall()

                conn.commit()
                conn.close()

                if outcome != ():
                    return True
    return False


def remove_npc_npc_association(npc_1_id, npc_2_id, user_id, session_key):
    """
    This function will remove an association between
    an npc and an npc from the linker table

    :param npc_1_id: the id of the npc
    :param npc_2_id: the id of the city
    :param user_id: the id of the user requesting this
    :param session_key: the user's session key

    :return: True if successful, False if not
    """
    if check_session_key(user_id, session_key):
        world_id = check_same_world(npc_1_id, npc_2_id)

        if world_id > 0:
            if check_editable(world_id, user_id, session_key):
                conn = connect()
                cur = conn.cursor()

                delete_request = """
                    DELETE FROM npc_npc_linker WHERE
                    npc_1_id = %s AND npc_2_id = %s
                    """
                cur.execute(delete_request, (npc_1_id, npc_2_id))
                conn.commit()
                conn.close()
                return True
    return False


def get_associated_npcs(user_id, session_key, npc_id):
    """
    This function will get a list of npcs who
    are associated with the specified npc
    :param user_id: the is of the user requesting
    :param session_key: the user's session key
    :param npc_id: the id of the npc being checked

    :return: a list with a dictionary of the values

    :format return: [{ id: npc id,
                       name: npc name}]
    """
    npc_list = []

    if check_session_key(user_id, session_key):
        conn = connect()
        cur = conn.cursor()

        world_id_check = """
            SELECT world_id FROM npcs
            WHERE id = %s
            """
        cur.execute(world_id_check, [npc_id])
        world_id = cur.fetchall()[0][0]
        npc_1_results = []
        npc_2_results = []

        if check_editable(world_id, user_id, session_key):
            npc2_query = """
                SELECT npcs.id, name FROM npc_npc_linker
                    INNER JOIN npcs ON npc_npc_linker.npc_2_id = npcs.id
                WHERE npc_1_id = %s
                """
            npc1_query = """
                    SELECT npcs.id, name FROM npc_npc_linker
                        INNER JOIN npcs ON npc_npc_linker.npc_1_id = npcs.id
                    WHERE npc_2_id = %s
                    """
            npc_1_results = cur.execute(npc1_query, [npc_id])
            npc_2_results = cur.execute(npc2_query, [npc_id])
        else:
            if check_viewable(world_id, user_id):
                npc2_query = """
                    SELECT npcs.id, name FROM npc_npc_linker
                        INNER JOIN npcs ON npc_npc_linker.npc_2_id = npcs.id
                    WHERE npc_1_id = %s AND npcs.revealed = 't'
                    """
                npc1_query = """
                    SELECT npcs.id, name FROM npc_npc_linker
                        INNER JOIN npcs ON npc_npc_linker.npc_1_id = npcs.id
                    WHERE npc_2_id = %s AND npcs.revealed = 't'
                    """
                npc_1_results = cur.execute(npc1_query, [npc_id])
                npc_2_results = cur.execute(npc2_query, [npc_id])

        for npc in npc_1_results:
            npc_list.append(({'id': npc[0],
                              'name': npc[1]}))

        for npc in npc_2_results:
            npc_list.append(({'id': npc[0],
                              'name': npc[1]}))

        conn.close()
    return npc_list
