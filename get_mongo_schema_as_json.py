#!/usr/bin/env python

"""Read data from mongo collection and create 'schema' that
corresponding to read data. Export schema as json."""

import sys
import json
import argparse
import bson
import datetime
import pymongo
from pymongo.mongo_client import MongoClient

def message(mes, cr='\n'):
    sys.stderr.write( mes + cr)

def assign_val_to_schema_key(val, schema, key):
    if type(val) is type:
        schema[key] = val
    elif type(val) is list and len(val)>0 and val[0] is not type(None):
        schema[key] = val
    elif type(schema[key]) == None or type(schema[key]) == type(None) or \
            ( (type(schema[key]) is dict or type(schema[key]) is list) \
                  and len(val) >= len(schema[key]) ) :
        if val is not type(None) or schema[key] == None or type(schema[key]) == type(None):
            schema[key] = val

def get_mongo_collection_schema(source_data, schema):
    if type(source_data) is dict:
        if type(schema) is not dict:
            schema = {}
        for key in source_data:
            nested_schema = {}
            #add to schema
            if ( schema.get(key) == None ):
                schema[key] = {}
            else:
                nested_schema = schema[key]
            tmp_schema = get_mongo_collection_schema(source_data[key], nested_schema)
            assign_val_to_schema_key(tmp_schema, schema, key)

            #if key == 'associated_item_ids':
            #    print key, schema[key], tmp_schema
    elif type(source_data) is list:
        if type(schema) is list:
            schema_as_list = schema
        else:
            schema_as_list = [schema]
        nested_schema = schema_as_list
        for item in source_data:
            nested_schema[0] = get_mongo_collection_schema(item, nested_schema[0])
        #trying to resolve conflicts automatically
        if type(nested_schema[0]) == dict and len(nested_schema[0]) == 0:
            nested_schema = type(None)
        elif type(schema_as_list[0]) is dict and type(nested_schema[0]) is dict \
                and len(schema_as_list)>len(nested_schema):
            nested_schema = schema_as_list
        schema = nested_schema
    else:
        if type(source_data) is float:
            if (source_data - int(source_data)) > 0:
                schema = float
            else:
                schema = int
        elif type(source_data) is bson.objectid.ObjectId:
                schema = { 'oid': str, 'bsontype': int }
        else:
            schema = type(source_data)
    return schema

def python_type_as_str(t):
    if t is str or t is unicode:
        return "STRING"
    elif t is int:
        return "INT"
    elif t is float:
        return "DOUBLE"
    elif t is type(None):
        return "TINYINT"
    elif t is datetime.datetime:
        return "TIMESTAMP"
    elif t is bool:
        return "BOOLEAN"
    elif t is bson.int64.Int64:
        return "BIGINT"
    else:
        raise Exception("Can't handle type ", schema)


def prepare_schema_for_serialization(schema):
    if type(schema) is type:
        return python_type_as_str(schema)
    for key in schema:
        if type(schema[key]) is list:
            schema[key][0] = prepare_schema_for_serialization(schema[key][0])
        else:
            schema[key] = prepare_schema_for_serialization(schema[key])
    return schema


if __name__ == "__main__":
    
    default_request = '{}'

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="Mongo db host:port", type=str)
    parser.add_argument("-user", help="Mongo db user", type=str)
    parser.add_argument("-passw", help="Mongo db pass", type=str)
    parser.add_argument("-cn", "--collection-name", help="Mongo collection name that is expected in format db_name.collection_name", type=str)
    parser.add_argument("-of", action="store", 
                        help="File name with schema data encoded as json(stdout by default)", type=argparse.FileType('w'))
    parser.add_argument("-js-request", help='Mongo db search request in json format. default=%s' % (default_request), type=str)
    parser.add_argument("-rl", "--get-latest-records-limit", help='Max count of records sorted in descending order to be handled', type=int)

    args = parser.parse_args()

    if args.of == None:
        args.of = sys.stdout
        message( "using stdout for output schema")

    if args.host == None or args.collection_name == None:
        parser.print_help()
        exit(1)

    split_name = args.collection_name.split('.')
    if len(split_name) != 2:
        message("collection name is expected in format db_name.collection_name")
        exit(1)

    message("Connecting to mongo server "+args.host)
    split_host = args.host.split(':')
    if len(split_host) > 1:
        client = MongoClient(split_host[0], int(split_host[1]))
    else:
        client = MongoClient(args.host, 27017)

    if args.user or args.passw:
        client.quote_management.authenticate(args.user, args.passw)
        message("Authenticated")

    if args.js_request is None:
        args.js_request = default_request
    message( "Mongo request is: %s" % (args.js_request) )
    search_request = json.loads(args.js_request)

    db = client[split_name[0]]
    collection_names = db.collection_names()
    quotes = db[split_name[1]]

    rec_list = quotes.find( search_request )
    if args.get_latest_records_limit is not None:
        #in case of limit sort data to get most latest data
        rec_list.sort('_id', pymongo.DESCENDING)
        rec_list.limit(args.get_latest_records_limit)

    schema={}
    message("Handling records:")
    for r in rec_list:
        message(".", cr="")
        schema = get_mongo_collection_schema(r, schema)
    message("\nHandled %d records" % (rec_list.count(with_limit_and_skip=True)))

    schema = prepare_schema_for_serialization(schema)
    json.dump(schema, args.of, indent=4)
    message("Schema created")
