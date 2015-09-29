1. Get mongo collection's "schema" in json format. 
It will retrieve data from mongodb in according to request specified
in '-js-request' parameter. Note, that js values must be doublequoted
and doublequotes are escaped like here: "{\"_id\": {\"\$gt\":0}}"
Structure of schema and data types will be derived from data. In case
if field value is null it will assign TINYINT data type to schema's
field.

example: python get_mongo_schema_as_json.py --host localhost:27017 -cn db.collection -of schema.txt

Contents of resulted file schema.txt can be as following:
{
    "_id": "INT", 
    "some_field": "BOOLEAN", 
    "data": [
        {
            "_type": "STR", 
            "messages": [
                {
                    "date": "TIMESTAMP", 
                    "message": {
                        "type": "TINYINT", 
                        "text": "STR"
                    }
                }
            ]
        }
    ]
}

2.To get hiveql scripts for creating hive nested and native flat tables
see below. 
While generating external hive table it using content of template.txt
as template.  The lateral view is used for creating plain tables from
external table.
Some excessive table fields can be filtered by using 'ifeb' option,
just provide file with lines corresponding to data to be excluded.
Also to get all schema branches into file use option '-output-branches'.

exclude_list.txt: 
some_field
data.messages.message.type

example: python get_hiveql_create_tables_by_schema.py -ifs schema.txt -tn records -od hiveql_autogenerated -fexclude exclude_list.txt -output-branches all_branches.txt --mongouri mongodb://localhost:27017/db.collection

example: python get_mongo_schema_as_json.py --host localhost -cn db.collection | python get_hiveql_create_tables_by_schema.py -tn records -od hiveql_autogenerated -fexclude exclude_list.txt -output-branches all_branches.txt --mongouri mongodb://localhost:27017/db.collection

3.Known issues:
Generated tables may have duplicate fields due to naming conflicts, in
this case it's can be resolved manually by altering name of field in
produced file.
