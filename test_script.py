from sabpabot.mongo_access import mongo_db

mongo_db['Teams'].insert_one({'name': 'core', 'group_name': 'من و مادمازل و بات', 'team_type': 'general'})
