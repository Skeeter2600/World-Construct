from src.components.likes_dislikes import get_likes_dislike
from src.linkers.city_special_linker import get_cities_by_special
from src.linkers.npc_special_linker import get_npcs_by_special
from src.linkers.special_image_linker import get_associated_special_images
from src.utils.db_tools import check_session_key
from src.utils.db_utils import connect
from src.utils.permissions import check_editable


def rebuild_specials_table():
    """
    This function will empty the specials table
    """
    conn = connect()
    cur = conn.cursor()
    drop_sql = """
        DROP TABLE if EXISTS specials CASCADE;
        """
    create_sql = """
        CREATE TABLE specials(
            id                  SERIAL PRIMARY KEY,
            name                TEXT NOT NULL,
            description         TEXT NOT NULL,
            hidden_description  TEXT DEFAULT NULL,
            revealed            BOOLEAN NOT NULL DEFAULT 'f',
            edit_date           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            world_id            INTEGER NOT NULL REFERENCES worlds ON DELETE CASCADE
        )
        """
    cur.execute(drop_sql)
    cur.execute(create_sql)
    conn.commit()
    conn.close()


def add_special(user_id, session_key, details):
    """
    This function will add a new special to the world,
    given the user is an owner or admin

    :param user_id: the id of the user adding
    :param session_key: the user's session key
    :param details: the info on the new special

    :format details:{ world_id: world special is in,
                      name: special name,
                      images: [images associated with special],
                      description: city description,
                      hidden_description: the npc hidden description ('' if not used)
                      associated_cities: [id: city id],
                      associated_npcs: [id: npc id],
                      }

    :return: [created boolean, city id (-1 if failed)]
    """
    if check_editable(details['world_id'], user_id, session_key):
        conn = connect()
        cur = conn.cursor()

        if details['hidden_description'] == '':
            add_request = """
                        INSERT INTO specials(NAME, DESCRIPTION, hidden_description, WORLD_ID) 
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """
            cur.execute(add_request, (details['name'], details['description'],
                                      details['hidden_description'], details['world_id']))
        else:
            add_request = """
                INSERT INTO specials(NAME, DESCRIPTION, WORLD_ID) 
                VALUES (%s, %s, %s)
                RETURNING id
                """
            cur.execute(add_request, (details['name'], details['description'], details['world_id']))

        special_id = cur.fetchall()

        if special_id != ():
            special_id = special_id[0][0]

            if len(details['images']) > 0:
            # compile image list to add to special image linker
                image_add_request = """
                    INSERT INTO special_image_linker(special_id, image) VALUES
                    """
                add_values = ''
                length = len(details['images'])
                i = 0
                while i < length - 1:
                    add_values = add_values + '(' + str(special_id) + ', ' + str(details['images'][i]) + '), '
                    i += 1
                add_values = add_values + '(' + str(special_id) + ', ' + str(details['images'][i]) + ') '
                add_values = add_values + 'returning id'
                image_add_request = image_add_request + add_values

                cur.execute(image_add_request)
                outcome = cur.fetchall()
                if outcome == ():
                    return False

            if len(details['associated_cities']) > 0:
                # compile the city list to add to the linker
                city_add_request = """
                    INSERT INTO city_special_linker(city_id, special_id) VALUES
                    """
                add_values = ''
                length = len(details['associated_cities'])
                i = 0
                while i < length - 1:
                    add_values = add_values + '(' + str(details['associated_cities'][i]['id']) + ', ' + str(special_id) + '), '
                    i += 1
                add_values = add_values + '(' + str(details['associated_cities'][i]['id']) + ', ' + str(special_id) + ') '
                add_values = add_values + 'returning id'
                city_add_request = city_add_request + add_values

                cur.execute(city_add_request)
                outcome = cur.fetchall()
                if outcome == ():
                    return False

            if len(details['associated_npcs']) > 0:
                # compile the npc list to add to the linker
                npc_add_request = """
                    INSERT INTO npc_special_linker(npc_id, special_id) VALUES
                    """
                add_values = ''
                length = len(details['associated_npcs'])
                i = 0
                while i < length - 1:
                    add_values = add_values + '(' + str(details['associated_npcs'][i]['id']) + ', ' + str(special_id) + '), '
                    i += 1
                add_values = add_values + '(' + str(details['associated_npcs'][i]['id']) + ', ' + str(special_id) + ') '
                add_values = add_values + 'returning id'
                npc_add_request = npc_add_request + add_values

                cur.execute(npc_add_request)
                outcome = cur.fetchall()
                if outcome == ():
                    return False

            conn.commit()
            conn.close()
            return [True, special_id]
    return [False, -1]


def copy_special(user_id, session_key, special_id, world_id):
    """
    This function will make a copy of the specified special
    in the world of the user's choice, given they have permission
    to create new elements

    :param user_id: the id of the user requesting
    :param session_key: the session key of the user
    :param special_id: the id of the special
    :param world_id: the id of the world

    :return: the info of the new element if done, {} if failure
    """
    if check_editable(world_id, user_id, session_key):
        conn = connect()
        cur = conn.cursor()
        duplicate_request = """
            INSERT INTO specials(name, description, world_id)
            SELECT name, description, world_id FROM specials
            WHERE id = %s
            RETURNING id
            """
        cur.execute(duplicate_request, [special_id])
        new_id = cur.fetchall()[0][0]

        change_world = """
            UPDATE specials SET
            world_id = %s
            WHERE id = %s
            RETURNING id
            """
        cur.execute(change_world, (world_id, new_id))

        outcome = cur.fetchall()
        conn.commit()
        conn.close()
        if outcome != ():
            return [True, new_id]
    return [False, -1]


def delete_special(user_id, session_key, special_id, world_id):
    """
    This function will delete a npc from the world

    :param user_id: the id of the user requesting
    :param session_key: the session key of the user requesting
    :param special_id: id of the special
    :param world_id: id that the world is in

    :return: True if deleted, False if not
    """
    if check_session_key(user_id, session_key):
        if check_editable(world_id, user_id, session_key):
            conn = connect()
            cur = conn.cursor()

            delete_request = """
                DELETE FROM specials
                WHERE id = %s
                returning id
            """
            cur.execute(delete_request, [special_id])
            outcome = cur.fetchall()
            conn.commit()
            conn.close()

            if outcome != ():
                return True
    return False


def edit_special(user_id, session_key, special_id, world_id, details):
    """
    This function will modify the elements of a special
    in a world, give te user can edit it

    :param user_id: the id of the user editing
    :param session_key: the session_key of the user editing
    :param special_id: the id of the special being edited
    :param world_id: the id of the world the city is in
    :param details: the new info for the city

    :format details: { name: special name,
                       description: special description,
                       hidden_description: special hidden description
                       revealed: T or F,
                     }

    :return: the updated special info, {} if failure
    """
    if check_session_key(user_id, session_key):
        if check_editable(world_id, user_id, session_key):
            conn = connect()
            cur = conn.cursor()

            edit_request = """
                UPDATE specials SET
                name = %s, description = %s, revealed = %s, hidden_description = %s, edit_date = now()
                WHERE id = %s
                RETURNING id
                """
            cur.execute(edit_request, (details['name'], details['description'], details['revealed'], details['hidden_description'], special_id))
            outcome = cur.fetchall()

            if outcome == ():
                conn.close()
                return {}

            conn.commit()
            conn.close()

            return get_special_info(user_id, session_key, special_id, True)

    return {'name': '',
            'description': '',
            'hidden_description': '',
            'revealed': False}


def get_special_info(user_id, session_key, special_id, admin):
    """
    This function will get the information associated
    with an NPC based on the user's permissions
    :param special_id: the id of the npc being checked
    :param user_id: the id of the user checking
    :param session_key: the user's session key
    :param admin: if the user is an admin

    :return: the npc info in a json format

    :format return: { name: special name,
                      images: [images associated with special],
                      like_dislike_info: {
                          likes: int of likes,
                          dislikes: int of dislikes
                          user_like: is user liked it (True or False),
                          user_dislike: is user disliked it (True or False)
                      }
                      description: npc description,
                      associated_npcs: [{id: npc id,
                                         name: npc name}]
                      associated_cities: [{id: city id,
                                           name: city name}],
                      admin_content: {
                            hidden_description: npc hidden description,
                            revealed: T or F,
                            edit_date: last time updated
                      } (empty if not admin)
    """
    special_info = {'name': '',
                    'images': [],
                    'like_dislike_info':
                        {'likes': 0,
                         'dislikes': 0,
                         'user_like': False,
                         'user_dislike': False
                         },
                    'description': "",
                    'associated_npcs': [],
                    'associated_cities': [],
                    'admin_content': {}}

    if check_session_key(user_id, session_key):
        conn = connect()
        cur = conn.cursor()

        all_info_query = """
            SELECT name, description FROM specials
            WHERE id = %s
            """

        if not admin:
            all_info_query = all_info_query + " AND revealed = 't'"

        cur.execute(all_info_query, [special_id])
        all_outcome = cur.fetchall()
        if len(all_outcome) > 0:
            all_outcome = all_outcome[0]
            special_info['name'] = all_outcome[0]

            special_info['images'] = get_associated_special_images(special_id)

            special_info['description'] = all_outcome[1]

            special_info['associated_npcs'] = get_npcs_by_special(user_id, session_key, special_id)
            special_info['associated_cities'] = get_cities_by_special(user_id, session_key, special_id)

            if admin:
                admin_content = {'hidden_description': '',
                                 'revealed': None,
                                 'edit_date': ''
                                 }
                admin_query = """
                    SELECT hidden_description, revealed, edit_date FROM specials
                    WHERE id = %s
                    """
                cur.execute(admin_query, [special_id])
                admin_outcome = cur.fetchall()[0]

                admin_content['hidden_description'] = admin_outcome[0]
                admin_content['revealed'] = admin_outcome[1]
                admin_content['edit_date'] = admin_outcome[2]

                special_info['admin_content'] = admin_content

            special_info['like_dislike_info'] = get_likes_dislike(user_id, special_id, 'specials')

        conn.close()

    return special_info


def reveal_hidden_special(user_id, session_key, world_id, special_id):
    """
    This function will reveal the hidden description by amending
    it to the description, given the user requesting has edit permission

    :param user_id: id of the user requesting
    :param session_key: the user's session key
    :param world_id: the id of the world the special is in
    :param special_id: the id of the special to be revealed

    :return: The special's info if good, {} if bad
    """
    if check_editable(world_id, user_id, session_key):
        conn = connect()
        cur = conn.cursor()

        reveal_query = """
        UPDATE specials SET
        description = concat(description, '\n\nREVEAL\n\n', hidden_description),
        hidden_description = ''
        WHERE id = %s
        returning id
        """
        cur.execute(reveal_query, [special_id])
        outcome = cur.fetchall()
        conn.commit()
        conn.close()
        if outcome != ():
            return get_special_info(user_id, session_key, special_id, True)

    return {}


def search_for_special(param, world, limit, page, user_id, session_key):
    """
    This function will search for specials that contain the
    searched string within them.

    :param param: the string to search for
    :param world: the world to search in
    :param limit: the number of results to show
    :param page: the selection of elements to show
    :param user_id: the id of the user requesting
    :param session_key: the session key of the user requesting

    :return: the list of specials and their elements that
        meet the search requirements in json format

    :format return: [{ name: special name,
                       reveal_status: revealed(if admin)}]
    """
    special_list = []
    if check_session_key(user_id, session_key):
        conn = connect()
        cur = conn.cursor()

        if limit is None:
            limit = 25

        param = '%' + param + '%'

        if check_editable(world, user_id, session_key):
            request = """
                SELECT id, name, revealed FROM specials
                WHERE name ILIKE %s AND
                    specials.world_id = %s
                LIMIT %s OFFSET %s
            """
            cur.execute(request, (param, world, limit, (page - 1) * limit))
            specials_raw = cur.fetchall()
            for special in specials_raw:
                special_list.append({'id': special[0],
                                     'name': special[1],
                                     'reveal_status': special[2]})

        else:
            request = """
                SELECT id, name FROM specials
                WHERE name ILIKE %s AND
                    specials.world_id = %s AND specials.revealed = 't'
                LIMIT %s OFFSET %s
            """
            cur.execute(request, (param, world, limit, (page - 1) * limit))
            specials_raw = cur.fetchall()
            for special in specials_raw:
                special_list.append({'id': special[0],
                                     'name': special[1]})
        conn.close()

    return special_list

