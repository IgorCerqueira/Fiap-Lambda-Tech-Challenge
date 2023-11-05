import os
import json
import pymongo
import redis


class MongoDBClient:
    def __init__(self, cluster_endpoint, username, password, tls):
        self.client = pymongo.MongoClient(f"mongodb://{username}:{password}@{cluster_endpoint}:27017/?tls={tls}")

    def get_user_by_cpf(self, cpf):
        database = self.client['user']
        users_collection = database['users']
        user = users_collection.find_one({"cpf": cpf})
        return user


class RedisClient:
    def __init__(self, endpoint, port):
        self.client = redis.StrictRedis(host=endpoint, port=port, db=0, socket_timeout=5)

    def get_user_by_cpf(self, cpf):
        return self.client.get(cpf)

    def set_user(self, user):
        try:
            chave = user["cpf"]
            self.client.set(chave, json.dumps(user, default=str))
        except Exception as e:
            raise Exception(f"Erro ao adicionar usuário ao Redis: {e}")


def lambda_handler(event, context):
    if 'queryStringParameters' in event and 'cpf' in event['queryStringParameters']:
        cpf = event['queryStringParameters']['cpf']
        redis_client = RedisClient(os.environ["REDIS_CLUSTER"], os.environ["REDIS_PORT"])
        user = redis_client.get_user_by_cpf(cpf)

        if user:
            return {
                "statusCode": 200,
                "body": json.dumps(user, default=str)
            }

        mongo_client = MongoDBClient(os.environ["MONGO_CLUSTER"],
                                     os.environ["MONGO_LOGIN"], os.environ["MONGO_PASSW"], os.environ["MONGO_TLS"])
        user_mongo = mongo_client.get_user_by_cpf(cpf)

        if user_mongo:
            redis_client.set_user(user_mongo)
            return {
                "statusCode": 200,
                "body": json.dumps(user_mongo, default=str)
            }

        return {
            "statusCode": 404,
            "body": "Usuário não encontrado"
        }

    return {
        "statusCode": 400,
        "body": "Parâmetro não encontrado na URL - {event} - {event['queryStringParameters']}"
    }