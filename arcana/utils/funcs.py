#functions for the bot

function_list = [
    {
        "name": "search_database",
        "description": "Query the database and return a list of results as strings",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to execute against the database"
                },
            },
            "required": ["query"]
        }
    },

    {
        "name": "list_database_files",
        "description": "Check what files are present in the database",
        "parameters":{
            "type":"object",
            "properties":{
                "query":{
                    "type":"string",
                    "description":"Gives a list of semicolon seperated file names in the database"
                    },
                },
        }
    }
]

# Mapping of function names to actual function objects
function_map = {
    "search_database": query_database2,
    "list_database_files":list_files_indb
}
