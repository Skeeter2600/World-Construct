from flask import Flask
from flask_restful import Api
from api.hello_world import HelloWorld
from api.user import UserAccountPublic, AccountInfo, LoginLogout, UserSearch
from api.world import WorldManagement, JoinWorldPublic, JoinWorldPrivate, WorldOwner, WorldUserList, WorldDetails, WorldSearch
from api.special import SpecialManagement, CopySpecial, RevealSpecial, SpecialDetails, SpecialSearch
from api.city import CitySearch, CityDetails, CopyCity, CityManagement
from api.npc import NPCManagement, CopyNPC, RevealNPC, NPCDetails, NPCSearch
from api.comment import CommentDetails, CommentManagement, ComponentComments, UserComments

app = Flask(__name__)
api = Api(app)

api.add_resource(HelloWorld, '/')
api.add_resource(UserAccountPublic, f'/user/<int:user_id>')
api.add_resource(AccountInfo, '/user/')
api.add_resource(LoginLogout, '/user/log')
api.add_resource(UserSearch, '/search/user/<string:param>/<int:limit>/<int:page>/')
api.add_resource(WorldManagement, '/world/manage')
api.add_resource(JoinWorldPublic, '/world/join/public/')
api.add_resource(JoinWorldPrivate, '/world/join/private/')
api.add_resource(WorldOwner, 'world/<int:world_id>/owner')
api.add_resource(WorldUserList, 'world/<int:world_id>/users')
api.add_resource(WorldDetails, '/world/<int:world_id>')
api.add_resource(WorldSearch, '/search/world/<string:param>/<int:limit>/<int:page>/')
api.add_resource(SpecialManagement, '/special/manage')
api.add_resource(CopySpecial, '/special/copy/<int:special_id>')
api.add_resource(RevealSpecial, '/special/reveal/<int:world_id>/<int:special_id>')
api.add_resource(SpecialDetails, '/special/<int:special_id>')
api.add_resource(SpecialSearch, '/search/special/<int:world_id>/<string:param>/<int:limit>/<int:page>/')
api.add_resource(CityManagement, '/city/manage/')
api.add_resource(CopyCity, '/city/copy/<int:city_id>')
api.add_resource(CityDetails, '/city/<int:city_id>')
api.add_resource(CitySearch, '/search/city/<int:world_id>/<string:param>/<int:limit>/<int:page>/')
api.add_resource(NPCManagement, '/npc/manage')
api.add_resource(CopyNPC, '/npc/copy/<int:npc_id>')
api.add_resource(RevealNPC, '/npc/reveal/<int:world_id>/<int:npc_id>')
api.add_resource(NPCDetails, '/npc/<int:npc_id>')
api.add_resource(NPCSearch, '/search/npc/<int:world_id>/<string:param>/<int:limit>/<int:page>/')
api.add_resource(CommentManagement, '/comment/manage/')
api.add_resource(CommentDetails, '/comment/<int:comment_id>')
api.add_resource(ComponentComments, '/comment/<int:component_table>/<int:comment_id>')
api.add_resource(UserComments, '/user/<int:user_id>/comments/<int:limit>/<int:page>/')


if __name__ == '__main__':
    app.run(debug=True)
    