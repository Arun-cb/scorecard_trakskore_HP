from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status, filters
import mysql.connector as sqlConnect
from .serializers import *
import cx_Oracle
from django.db.models import F, Q
import snowflake.connector
import pandas as pd
from ydata_profiling import ProfileReport
from datetime import datetime
import json
import numpy as np


@api_view(["POST"])
def set_db_sql_connection(request):
    reqconnData = request.data
    
    try:
        db_type = reqconnData.get('connection_type')
        
        if db_type == 'MYSQL':
            try:
                mydb = sqlConnect.connect(
                    host=reqconnData.get('host_id'),
                    user=reqconnData.get('user_name'),
                    password=reqconnData.get('password'),
                    database=reqconnData.get('database_name'),
                    port=reqconnData.get('port')
                )
                
                # Check if the connection is successful
                if mydb.is_connected():
                    mydb.close()
                    return Response('Connected', status=status.HTTP_200_OK)
                else:
                    return Response("Failed", status=status.HTTP_400_BAD_REQUEST)
                
            except sqlConnect.Error as e:
                # Handle the database-related errors, including syntax errors
                error_message = str(e)

                return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

        elif db_type == "Oracle":
            try:
                connection_str = f"{reqconnData.get('user_name')}/{reqconnData.get('password')}@{reqconnData.get('host_id')}:{reqconnData.get('port')}/{reqconnData.get('service_name_or_SID')}"
                if cx_Oracle.connect(connection_str):
                    connection = cx_Oracle.connect(connection_str)
                    connection.close()
                    return Response("Connected", status=status.HTTP_200_OK)
                else:
                    return Response("Failed", status=status.HTTP_400_BAD_REQUEST)
            
            except cx_Oracle.Error as e:
                # Handle Oracle errors
                error_message = f"Oracle error: {str(e)}"
                return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

        elif db_type == "Snowflake":
            try:
                # Build the connection string
                connection_str = {
                    'user': reqconnData.get('user_name'),
                    'password': reqconnData.get('password'),
                    'account': reqconnData.get('account_id'),
                    'warehouse': reqconnData.get('warehouse_id'),
                    'database': reqconnData.get('database_name'),
                    'schema': reqconnData.get('schema_name'),
                    'role': reqconnData.get('role'),
                }

                if snowflake.connector.connect(**connection_str):
                    connection = snowflake.connector.connect(**connection_str)
                    print("connection", connection)
                    connection.close()
                    return Response('Connected', status=status.HTTP_200_OK)
                else:
                    return Response('Failure', status=status.HTTP_400_BAD_REQUEST)
            
            except snowflake.connector.errors.DatabaseError as e:
                # Handle Oracle errors
                error_message = f"Oracle error: {str(e)}"
                print("error_message", error_message)
                return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response('Database not found!', status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        # Handle any database connection errors
        return Response(f'Database connection error: {str(e)}', status=status.HTTP_400_BAD_REQUEST)


# Query Defnition
@api_view(["POST"])
def fnStoreQueryNameConnectionData(request):

    connnectionrequestdata = request.data

    postConnData = {
        "query_name": connnectionrequestdata.get("query_name"),
        "connection_id": connnectionrequestdata["savedConnectionItems"].get("id"),
        "query_text": connnectionrequestdata.get("query_name")
        if request.data.get("query_text") == None
        else request.data.get("query_text"),
        "query_status": False
        if request.data.get("query_status") == None
        else request.data.get("query_status"),
        "query_type": False
        if request.data.get("query_type") == None
        else request.data.get("query_type"),
        "created_user": connnectionrequestdata.get("created_user"),
        "created_by": connnectionrequestdata.get("created_by"),
        "last_updated_by": connnectionrequestdata.get("last_updated_by")
    }

    queryDefnitionSerilazier = qb_defnition_serializer(data=postConnData)

    if queryDefnitionSerilazier.is_valid():
        queryDefnitionSerilazier.save()
        return Response(queryDefnitionSerilazier.data, status=status.HTTP_201_CREATED)

    return Response(queryDefnitionSerilazier.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def fnUpdateQueryNameConnectionData(request, id):
    item = query_definition.objects.get(id=id)

    serializer = qb_defnition_serializer(instance=item, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def fnGetQueryDefinition(request, id=0):
    if id == 0:
        queryDefinitionData = query_definition.objects.filter(delete_flag="N")
    else:
        queryDefinitionData = query_definition.objects.filter(id=id)

    definitionSerializer = qb_defnition_serializer(
        queryDefinitionData, many=True)
    return Response(definitionSerializer.data, status=status.HTTP_200_OK)

# ? GET Range Query Definition


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_range_query_definition(request, start, end, created_user, sortcolumn, search=False):
    try:
        if not search:
            query_def_len = query_definition.objects.filter(
                delete_flag="N", created_user=created_user).count()
            query_def = query_definition.objects.filter(
                delete_flag="N", created_user=created_user).order_by(sortcolumn)[start:end]
        else:
            query_def_len = query_definition.objects.filter(Q(query_name__icontains=search) | Q(created_by__icontains=search) | Q(
                created_date__icontains=search), delete_flag="N", created_user=created_user).count()
            query_def = query_definition.objects.filter(Q(query_name__icontains=search) | Q(created_by__icontains=search) | Q(
                created_date__icontains=search), delete_flag="N", created_user=created_user).order_by(sortcolumn)[start:end]
        query_def_csv_export = query_definition.objects.filter(
            delete_flag="N", created_user=created_user)
        serializer = qb_defnition_serializer(query_def, many=True)
        # print(type(json.loads(json.dumps(serializer.data))), json.dumps(serializer.data))
        temp_data = []
        for data in json.loads(json.dumps(serializer.data)):
            con_data = data['connection_id']
            del data['connection_id']
            data['connection_id'] = con_data['id']
            data['connection_type'] = con_data['connection_type']
            temp_data.append(data)
        serializer_csv_export = qb_defnition_serializer(
            query_def_csv_export, many=True)
        return Response(
            {
                "data": temp_data,
                "data_length": query_def_len,
                "csv_data": serializer_csv_export.data,
            }
        )

    except Exception as e:
        return Response(f"exception:{e}", status=status.HTTP_400_BAD_REQUEST)

# ? Shared Query

# Query Defnition


@api_view(["POST"])
def ins_shared_query_definition(request):

    sharedquerydata = request.data

    if request.data.get("permission_to_edit") != None:
        for i in range(len(sharedquerydata["permission_to_edit"])):
            insshareEditData = {
                "permission_to": sharedquerydata["permission_to_edit"][i],
                "permission_by": sharedquerydata.get("permission_by"),
                "permission_type": "Editable",
                "query_id": sharedquerydata.get("query_id"),
                "created_by": sharedquerydata.get("created_by"),
                "last_updated_by": sharedquerydata.get("last_updated_by")
            }

            shareEditserializer = shared_query_definition_serializer(
                data=insshareEditData)
            if shareEditserializer.is_valid():
                shareEditserializer.save()
            else:
                return Response(shareEditserializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("permission_to_view") != None:
        for i in range(len(sharedquerydata["permission_to_view"])):
            insshareViewData = {
                "permission_to": sharedquerydata["permission_to_view"][i],
                "permission_by": sharedquerydata.get("permission_by"),
                "permission_type": "Read only",
                "query_id": sharedquerydata.get("query_id"),
                "created_by": sharedquerydata.get("created_by"),
                "last_updated_by": sharedquerydata.get("last_updated_by")
            }

            shareViewserializer = shared_query_definition_serializer(
                data=insshareViewData)
            if shareViewserializer.is_valid():
                shareViewserializer.save()
            else:
                return Response(shareViewserializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(request.data, status=status.HTTP_201_CREATED)

    # inssharedData = {
    #     "permission_to" : sharedquerydata.get("permission_to"),
    #     "permission_by" : sharedquerydata.get("permission_by"),
    #     "permission_type" : sharedquerydata.get("permission_type"),
    #     "query_id" : sharedquerydata.get("query_id"),
    #     "created_by" : sharedquerydata.get("created_by"),
    #     "last_updated_by" : sharedquerydata.get("last_updated_by")
    # }

    # sharedqueryDefnitionSerilazier =shared_query_definition_serializer(data=inssharedData)

    # if sharedqueryDefnitionSerilazier.is_valid():
    #     sharedqueryDefnitionSerilazier.save()
    #     return Response(sharedqueryDefnitionSerilazier.data,status = status.HTTP_201_CREATED)
    # else:
    #     return Response(sharedqueryDefnitionSerilazier.errors,status=status.HTTP_400_BAD_REQUEST)

    # return Response("sharedqueryDefnitionSerilazier.errors",status = status.HTTP_201_CREATED)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upd_shared_query_definition(request, id):
    item = shared_query_definition.objects.get(id=id)

    serializer = shared_query_definition_serializer(
        instance=item, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_shared_query_definition(request, id=0):
    if id == 0:
        queryDefinitionData = shared_query_definition.objects.filter(
            delete_flag="N")
    else:
        queryDefinitionData = shared_query_definition.objects.filter(id=id)

    definitionSerializer = shared_query_definition_serializer(
        queryDefinitionData, many=True)
    return Response(definitionSerializer.data, status=status.HTTP_200_OK)

# ? GET Range Shared Query Definition


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_range_shared_query_definition(request, start, end, permission_to, sortcolumn, search=False):
    try:
        if not search:
            query_def_len = shared_query_definition.objects.filter(
                delete_flag="N", permission_to=permission_to).count()
            query_def = shared_query_definition.objects.filter(
                delete_flag="N", permission_to=permission_to).order_by("query_id")
        else:
            query_def = shared_query_definition.objects.filter(Q(query_name__icontains=search) | Q(created_by__icontains=search) | Q(
                created_date__icontains=search), delete_flag="N", permission_to=permission_to).order_by("query_id")[start:end]
        serializer = shared_query_definition_serializer(query_def, many=True)
        print("ser",serializer.data)

        # ? List Of Query Id's
        shared_query_ids = [item['query_id'] for item in serializer.data]

        if not search:
            shared_query_def_len = query_definition.objects.filter(
                delete_flag="N", id__in=shared_query_ids).count()
            shared_query_def = query_definition.objects.filter(
                delete_flag="N", id__in=shared_query_ids).order_by(sortcolumn)[start:end]
        else:
            shared_query_def_len = query_definition.objects.filter(Q(query_name__icontains=search) | Q(
                created_by__icontains=search) | Q(created_date__icontains=search), delete_flag="N", id__in=shared_query_ids).count()
            shared_query_def = query_definition.objects.filter(Q(query_name__icontains=search) | Q(
                created_by__icontains=search) | Q(created_date__icontains=search), delete_flag="N", id__in=shared_query_ids).order_by(sortcolumn)[start:end]
        shared_query_def_csv_export = query_definition.objects.filter(
            delete_flag="N", id__in=shared_query_ids)
        shared_serializer = qb_defnition_serializer(
            shared_query_def, many=True)

        shared_serializer_csv_export = qb_defnition_serializer(
            shared_query_def_csv_export, many=True)

        return Response(
            {
                "data": shared_serializer.data,
                "data_length": query_def_len,
                "csv_data": shared_serializer_csv_export.data,
                "shared_data": serializer.data,
            }
        )

    except Exception as e:
        return Response(f"exception:{e}", status=status.HTTP_400_BAD_REQUEST)


# Selected Table
@api_view(["POST"])
def fnsaveSelectedTables(request):
    tableRequestData = request.data
    print("tableRequestData", tableRequestData)
    for i in range(len(tableRequestData)):
        selectedTableData = {
            "table_name": tableRequestData[i]["table_name"],
            "table_id": tableRequestData[i]["table_id"],
            "query_id": tableRequestData[i]["query_id"],
            "created_by": tableRequestData[i]["created_by"],
            "last_updated_by": tableRequestData[i]["last_updated_by"]
        }
        # exist_data = query_definition
        # id_to_update = tableRequestData[i].get("query_id")

        if "id" == None:
            queryTableInstance = query_definition.objects.get(id=id_to_update)
            queryTableserilizers = qb_table_serializer(
                instance=queryTableInstance, data=selectedTableData)

            if queryTableserilizers.is_valid():
                queryTableserilizers.save()
        else:
            queryTableSerilizers = qb_table_serializer(data=selectedTableData)

            if queryTableSerilizers.is_valid():
                queryTableSerilizers.save()
            else:
                return Response(queryTableSerilizers.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(selectedTableData, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def fnGetQueryBuilderTable(request, id=0):

    if id == 0:
        queryBuilderTable = query_builder_table.objects.filter(delete_flag="N")
    else:
        queryBuilderTable = query_builder_table.objects.filter(query_id=id)

    builderTableSerializer = qb_table_serializer(queryBuilderTable, many=True)
    return Response(builderTableSerializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def fnGetTableData(request):
    connnectionrequestdata = request.data
    saved_connection = connnectionrequestdata["savedConnectionItems"]
    
    db_type = saved_connection.get("connection_type")

    if db_type == 'MYSQL':

        mydb = sqlConnect.connect(
            host=saved_connection.get("host_id"),
            user=saved_connection.get("user_name"),
            password=saved_connection.get("password"),
            database=saved_connection.get("database_name"),
        )

        # Check if the connection is successful
        if mydb.is_connected():

            mycursor = mydb.cursor()

            table_schema = saved_connection.get("database_name")

            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE';"

            mycursor.execute(query, (table_schema,))

            table_names = [{"table_id": idx, "table_name": table[0]} for idx, table in enumerate(mycursor.fetchall(), start=1)]

            mycursor.close()

            mydb.close()

            return Response(table_names, status=status.HTTP_200_OK)

        else:
            return Response("Failed", status=status.HTTP_404_NOT_FOUND)

    elif db_type == "Oracle":

        connection_str = f"{saved_connection.get('user_name')}/{saved_connection.get('password')}@{saved_connection.get('host_id')}:{saved_connection.get('port')}/{saved_connection.get('service_name_or_SID')}"

        if cx_Oracle.connect(connection_str):

            mydb = cx_Oracle.connect(connection_str)

            # Create a cursor
            mycursor = mydb.cursor()

            # Query to retrieve table names from all_tables
            query = "SELECT table_name FROM all_tables WHERE owner = UPPER(:owner)"

            # Execute the query with the provided owner (schema)
            mycursor.execute(
                query, {'owner': saved_connection.get('user_name')})

            # Fetch all table names and create a list of dictionaries
            table_names = [{"table_id": idx, "table_name": table[0]} for idx, table in enumerate(mycursor.fetchall(), start=1)]
            
            mycursor.close()

            mydb.close()

            # Return the table names as a JSON response
            return Response(table_names, status=status.HTTP_200_OK)

        else:
            return Response("Failed", status=status.HTTP_404_NOT_FOUND)

    elif db_type == "Snowflake":

        # Build the connection string
        connection_str = {
            'user': saved_connection.get("user_name"),
            'password': saved_connection.get("password"),
            'account': saved_connection.get("account_id"),
            'warehouse': saved_connection.get("warehouse_id"),
            'database': saved_connection.get("database_name"),
            'schema': saved_connection.get("schema_name"),
            'role': saved_connection.get('role'),
        }

        # Attempt to connect to Snowflake
        connection = snowflake.connector.connect(**connection_str)

        # Create a cursor
        datacursor = connection.cursor()

        # Query to retrieve table names from information_schema.tables
        query = "SHOW TABLES"

        datacursor.execute(query)

        # Fetch all table names and create a list of dictionaries
        table_names = [{"table_id": idx, "table_name": table[1]} for idx, table in enumerate(datacursor.fetchall(), start=1)]

        datacursor.close()

        connection.close()

        # Return the table names as a JSON response
        return Response(table_names, status=status.HTTP_200_OK)

    else:

        return Response("Invalid database type", status=status.HTTP_400_BAD_REQUEST)


# Column Display , Insert and Get
@api_view(["POST"])
def rb_sql_show_columns(request):
    reqData = request.data
    connnectionrequestdata = reqData.get("getselectedConnections")
    reqTableColumnData = reqData.get("rightItems")

    saved_connection = connnectionrequestdata["savedConnectionItems"]

    db_type = saved_connection.get("connection_type")
    print("saved_connection", saved_connection)

    if db_type == 'MYSQL':

        mydb = sqlConnect.connect(
            host=saved_connection.get("host_id"),
            user=saved_connection.get("user_name"),
            password=saved_connection.get("password"),
            database=saved_connection.get("database_name"),
        )
        allResults = []
        print("MYSQL", mydb)
        for table_info in reqTableColumnData:
            tableName = table_info['table_name']
            tableId = table_info['table_id']
            dbCursor = mydb.cursor()
            dbCursor.execute(f"SHOW COLUMNS FROM {tableName}")
            results = [{"columnName": row[0], "dataType": row[1].split(
                '(')[0], "tableId": tableId} for idx, row in enumerate(dbCursor.fetchall(), start=1)]
            # results = [{"id": idx, "columnName": row[0], "dataType": row[1].split(
            #     '(')[0], "tableId": tableId} for idx, row in enumerate(dbCursor.fetchall(), start=1)]
            # print("results", results)
            tableResults = {tableName: results}
            allResults.append(tableResults)
            dbCursor.close()
        mydb.close()
        return Response(allResults, status=status.HTTP_200_OK)

    elif db_type == "Oracle":

        connection_str = f"{saved_connection.get('user_name')}/{saved_connection.get('password')}@{saved_connection.get('host_id')}:{saved_connection.get('port')}/{saved_connection.get('service_name_or_SID')}"

        if cx_Oracle.connect(connection_str):

            mydb = cx_Oracle.connect(connection_str)

            # Create a cursor
            mycursor = mydb.cursor()

            # Query to retrieve table names from all_tables
            query = "SELECT table_name FROM all_tables WHERE owner = UPPER(:owner)"

            # Execute the query with the provided owner (schema)
            mycursor.execute(
                query, {'owner': saved_connection.get('user_name')})

            # Fetch all table names and create a list of dictionaries
            table_names = [{"table_id": idx, "table_name": table[0]} for idx, table in enumerate(mycursor.fetchall(), start=1)]

            mycursor.close()

            mydb.close()

            # Return the table names as a JSON response
            return Response(table_names, status=status.HTTP_200_OK)

        else:
            return Response("Failed", status=status.HTTP_404_NOT_FOUND)

    elif db_type == "Snowflake":

        # Build the connection string
        connection_str = {
            'user': saved_connection.get("user_name"),
            'password': saved_connection.get("password"),
            'account': saved_connection.get("account_id"),
            'warehouse': saved_connection.get("warehouse_id"),
            'database': saved_connection.get("database_name"),
            'schema': saved_connection.get("schema_name"),
            'role': saved_connection.get('role'),
        }
        allResults = []
        # Attempt to connect to Snowflake
        connection = snowflake.connector.connect(**connection_str)
        for table_info in reqTableColumnData:
            
            tableName = table_info['table_name']
            
            tableId = table_info['table_id']
            
            dbCursor = connection.cursor()
            
            dbCursor.execute(f"SHOW COLUMNS in TABLE {tableName}")
            
            results = [{"id": idx, "columnName": row[2], "dataType": json.loads(row[3])['type'], "tableId": tableId} 
            for idx, row in enumerate(dbCursor.fetchall())]
            
            tableResults = {tableName: results}
            
            allResults.append(tableResults)

            dbCursor.close()

        connection.close()
        
        return Response(allResults, status=status.HTTP_200_OK)
    
    else:
        return Response("Invalid database type", status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def fnsaveSelectedColumn(request):
    reqColumnData = request.data
    
    for table_data in reqColumnData:
        for column_data in table_data["table_columns"]:
            postData = {
                "table_column_query_id": table_data["query_id"],
                "column_name": column_data["columnName"],
                "alias_name": None if column_data["setAliasName"] is None else column_data["setAliasName"],
                "table_column_table_id": column_data["tableId"],
                "created_by": table_data["created_by"],
                "last_updated_by": table_data["last_updated_by"],
            }
                      
            postcolumnserilizers = qb_table_columns_serializers(data=postData)
            
            if postcolumnserilizers.is_valid():
                postcolumnserilizers.save()
            else:
                return Response(postcolumnserilizers.errors,status=status.HTTP_400_BAD_REQUEST)
            
    return Response(postData,status=status.HTTP_200_OK)


@api_view(["GET"])
def fngetsavedcolumns(request, id=0):

    if id == 0:
        savedcolumnsData = query_builder_table_columns.objects.filter(
            delete_flag="N")
    else:
        savedcolumnsData = query_builder_table_columns.objects.filter(
            table_column_query_id=id)

    saveColumnDataSerializers = qb_table_columns_serializers(
        savedcolumnsData, many=True)
    return Response(saveColumnDataSerializers.data, status=status.HTTP_200_OK)

# join table post and get


@api_view(["POST"])
def fninsjointablesave(request):
    reqjointabledata = request.data
    for i in range(len(reqjointabledata)):
        listofjointabledata = {
            "join_type": reqjointabledata[i]["selectedAttribute"],
            "join_column_name1": reqjointabledata[i]["selectedColumn"],
            "join_column_name2": reqjointabledata[i]["selectedColumn2"],
            "tab_join_query_id": reqjointabledata[i]["query_id"],
            "tab_join_table_id_one": reqjointabledata[i]["tableid1"],
            "tab_join_table_id_two": reqjointabledata[i]["tableid2"],
            "created_by": reqjointabledata[i]["created_by"],
            "last_updated_by": reqjointabledata[i]["last_updated_by"]
        }

        joinTableDataSerializers = qb_table_joins_serializers(
            data=listofjointabledata)

        if joinTableDataSerializers.is_valid():
            joinTableDataSerializers.save()
        else:
            return Response(joinTableDataSerializers.errors,status = status.HTTP_400_BAD_REQUEST)
            
    return Response(joinTableDataSerializers.data,status=status.HTTP_200_OK)   


@api_view(["GET"])
def fnGetJoinTableColumnData(request, id=0):

    if id == 0:
        savedJoinTableColumData = query_builder_table_joins.objects.filter(
            delete_flag="N")
    else:
        savedJoinTableColumData = query_builder_table_joins.objects.filter(
            tab_join_query_id=id)

    savedJoinTableSerializers = qb_table_joins_serializers(
        savedJoinTableColumData, many=True)
    return Response(savedJoinTableSerializers.data, status=status.HTTP_200_OK)


# Column Alias Post and Get
@api_view(["PUT"])
def fn_ins_column_alias(request):
    request_alias_data = request.data

    for column_data in request_alias_data:
        post_data = {
            "table_column_query_id": column_data["query_id"],
            "column_name": column_data["selectedColumnName"],
            "alias_name": column_data["setAliasName"],
            "table_column_table_id": column_data["aliastableId"],
            "created_by": column_data["created_by"],
            "last_updated_by": column_data["last_updated_by"],
        }

        # Filter data based on table_column_query_id
        alias_table_data = query_builder_table_columns.objects.filter(
            table_column_query_id=post_data["table_column_query_id"])

        # Convert the queryset to a list before passing it to the serializer
        alias_table_data_list = list(alias_table_data)

        # Update data using the serializer
        alias_table_data_serializer = qb_table_columns_serializers(
            instance=alias_table_data_list[0], data=post_data)

        if alias_table_data_serializer.is_valid():
            alias_table_data_serializer.save()
            return Response({"message": "Data updated successfully"}, status=status.HTTP_200_OK)

        else:
            return Response(alias_table_data_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def fn_get_column_alias(request):
    savedAliasTableColumData = query_builder_table_alias.objects.filter(
        delete_flag="N")
    savedAliasTableSerializers = qb_table_alias_serializers(
        savedAliasTableColumData, many=True)
    return Response(savedAliasTableSerializers.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def fn_ins_column_aggregate(request):
    requestAggregateData = request.data
    for i in range(len(requestAggregateData)):
        listofaggregatetabledata = {
            "agg_fun_name": requestAggregateData[i]["selectedAttribute"],
            "table_aggragate_query_id": requestAggregateData[i]["query_id"],
            "table_aggregate_table_id": requestAggregateData[i]["aggregatetableId"],
            "table_aggregate_column_id": requestAggregateData[i]["aggregatecolumnId"],
            "created_by": requestAggregateData[i]["created_by"],
            "last_updated_by": requestAggregateData[i]["last_updated_by"]
        }

        aggregateserializers = qb_table_aggergate_serializers(
            data=listofaggregatetabledata)

        if aggregateserializers.is_valid():
            aggregateserializers.save()
        else:
            return Response(aggregateserializers.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(aggregateserializers.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def fn_get_column_aggregate(request, id=0):

    if id == 0:
        savedAggregatedTableColumData = query_builder_aggeration_function_table.objects.filter(
            delete_flag="N")
    else:
        savedAggregatedTableColumData = query_builder_aggeration_function_table.objects.filter(
            table_aggragate_query_id=id)

    savedAggregatedTableSerializers = qb_table_aggergate_serializers(
        savedAggregatedTableColumData, many=True)
    return Response(savedAggregatedTableSerializers.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def fn_ins_column_filter_data(request):
    requestfilterdata = request.data
    for i in range(len(requestfilterdata)):
        listfiltercolumndata = {
            "column_name": requestfilterdata[i]["column_name"],
            "column_filter": requestfilterdata[i]["operator"],
            "column_value": f"{requestfilterdata[i]['start_value']},{requestfilterdata[i]['end_value']}",
            "tab_filter_query_id": requestfilterdata[i]["query_id"],
            "tab_filter_tale_id": requestfilterdata[i]["tab_filter_tale_id"],
            "created_by": requestfilterdata[i]["created_by"],
            "last_updated_by": requestfilterdata[i]["last_updated_by"]
        }

        
        columnfilterserializer = qb_table_column_filter_serializers(
            data=listfiltercolumndata)

        if columnfilterserializer.is_valid():
            columnfilterserializer.save()
        else:
            return Response(columnfilterserializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(columnfilterserializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def fn_ins_column_filter_data(request):
    requestfilterdata = request.data
    
    for i in range(len(requestfilterdata)):
        listfiltercolumndata ={
            "column_name" : requestfilterdata[i]["column_name"],
            "column_filter" : requestfilterdata[i]["operator"],
            "column_value": f"{requestfilterdata[i]['start_value']},{requestfilterdata[i]['end_value']}",
            "tab_filter_query_id" : requestfilterdata[i]["query_id"],
            "tab_filter_tale_id" : requestfilterdata[i]["tab_filter_tale_id"],
            "created_by" : requestfilterdata[i]["created_by"],
            "last_updated_by" : requestfilterdata[i]["last_updated_by"]
        }
        
        
        
        columnfilterserializer = qb_table_column_filter_serializers(data = listfiltercolumndata)
        
        
        if columnfilterserializer.is_valid():
            columnfilterserializer.save()
        else:
            return Response(columnfilterserializer.errors,status=status.HTTP_400_BAD_REQUEST)
            
    return Response(columnfilterserializer.data,status=status.HTTP_200_OK)
    

# Execute Query
@api_view(["POST"])
def fnpostquerytoexecute(request):
    queryText = request.data

    mydb = sqlConnect.connect(
        host="localhost",
        user="root",
        password="",
        database="score_card"
    )

    dbCursor = mydb.cursor(dictionary=True)
    dbCursor.execute(queryText)
    columns = [column[0] for column in dbCursor.description]
    results = dbCursor.fetchall()
    response_data = [{'columns': columns, 'data': results}]
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
def set_db_oracle_connection(request):
    mydb = cx_Oracle.connect(
        'sys/Admin123@localhost:1521/orcl', mode=cx_Oracle.SYSDBA)
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM smpletable")
    columns = [col[0] for col in mycursor.description]
    results = [dict(zip(columns, row)) for row in mycursor.fetchall()]
    return Response(results, status=status.HTTP_200_OK)


# Test API FOR QUERY EXECUTION
@api_view(["POST"])
def fnGetQueryResult(request):
    connnectionrequestdata = request.data

    saved_connection = connnectionrequestdata["savedConnectionItems"]
    query = connnectionrequestdata["query_text"]
    
    db_type = saved_connection.get("connection_type")

    if db_type == 'MYSQL':

        try:

            mydb = sqlConnect.connect(
                host=saved_connection.get("host_id"),
                user=saved_connection.get("user_name"),
                password=saved_connection.get("password"),
                database=saved_connection.get("database_name"),
            )

            mycursor = mydb.cursor(dictionary=True)

            if query:
                mycursor.execute(query)
                
                columns = [column[0] for column in mycursor.description]
                
                data_type_code = [col[1] for col in mycursor.description]
                
                mysql_default_type_code = {
                    0: 'DECIMAL',
                    1: 'TINYINT',
                    2: 'SMALLINT',
                    3: 'INTEGER',
                    4: 'FLOAT',
                    5: 'DOUBLE',
                    6: 'NULL',
                    7: 'TIMESTAMP',
                    8: 'BIGINT',
                    9: 'MEDIUMINT',
                    10: 'DATE',
                    11: 'TIME',
                    12: 'DATETIME',
                    13: 'YEAR',
                    14: 'NEWDATE',
                    15: 'VARCHAR',
                    16: 'BIT',
                    246: 'NEWDECIMAL',
                    247: 'INTERVAL',
                    248: 'SET',
                    249: 'TINY_BLOB',
                    250: 'MEDIUM_BLOB',
                    251: 'LONG_BLOB',
                    252: 'TEXT',
                    253: 'VARCHAR',
                    254: 'STRING',
                    255: 'GEOMETRY',
                }

                # Convert numeric data types to string representation
                data_types_str = [mysql_default_type_code.get(code, str(code)) for code in data_type_code]

                columns_info = [{'label': col, 'datatype': data_types_str[i]} for i, col in enumerate(columns)]
                
                results = mycursor.fetchall()
                
                response_data = [{'column_data': {"column" :columns, "type" : data_types_str}, 'data': results,"columns": columns_info}]

                mycursor.close()

                mydb.close()

                return Response(response_data, status=status.HTTP_200_OK)

            else:

                return Response({'error': "Query can't be blank"}, status=status.HTTP_400_BAD_REQUEST)

        except sqlConnect.Error as e:
            # Handle the database-related errors, including syntax errors
            error_message = str(e)

            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

    elif db_type == "Oracle":

        connection_str = f"{saved_connection.get('user_name')}/{saved_connection.get('password')}@{saved_connection.get('host_id')}:{saved_connection.get('port')}/{saved_connection.get('service_name_or_SID')}"

        cursor = None
        connection = None

        try:

            connection = cx_Oracle.connect(connection_str)

            # Create a cursor
            cursor = connection.cursor()

            if query:
                # Execute the queries
                cursor.execute(query)

                # Fetch columns and results
                columns = [column[0] for column in cursor.description]

                data_type_code = [col[1] for col in cursor.description]

                oracle_default_type_code = {
                    cx_Oracle.NUMBER: 'NUMBER',
                    cx_Oracle.STRING: 'VARCHAR',
                    cx_Oracle.FIXED_CHAR: 'CHAR',
                    cx_Oracle.DATETIME: 'DATE',
                    # Add other Oracle data types as needed
                }

                # Convert numeric data types to string representation
                data_types_str = [oracle_default_type_code.get(code, str(code)) for code in data_type_code]

                columns_info = [{'label': col, 'datatype': data_types_str[i]} for i, col in enumerate(columns)]

                results = cursor.fetchall()
                
                # Convert results to key-value pairs
                data = [dict(zip(columns, row)) for row in results]

                response_data = [{'column_data': {"column": columns, "type": data_types_str} , 'data': data, "columns": columns_info}]

                cursor.close()

                connection.close()

                return Response(response_data, status=status.HTTP_200_OK)

            else:

                return Response({'error': "Query can't be blank"}, status=status.HTTP_400_BAD_REQUEST)

        except cx_Oracle.Error as e:
            # Handle Oracle errors
            error_message = f"Oracle error: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

    elif db_type == "Snowflake":

        # Build the connection string
        connection_str = {
            'user': saved_connection.get("user_name"),
            'password': saved_connection.get("password"),
            'account': saved_connection.get("account_id"),
            'warehouse': saved_connection.get("warehouse_id"),
            'database': saved_connection.get("database_name"),
            'schema': saved_connection.get("schema_name"),
            'role': saved_connection.get('role'),
        }

        try:
            # Attempt to connect to Snowflake
            connection = snowflake.connector.connect(**connection_str)

            # Create a cursor
            cursor = connection.cursor()

            if query:
                # Execute the queries
                cursor.execute(query)

                # Fetch columns and results
                columns = [column[0] for column in cursor.description]
                
                data_type_code = [col.type_code for col in cursor.description]
                
                snowflake_default_type_code = {
                    0: 'NUMBER',
                    1: 'FLOAT',
                    2: 'VARCHAR',
                    3: 'DATE',
                    4: 'TIMESTAMP_TZ',
                    5: 'VARIANT',
                    6: 'OBJECT',
                    7: 'ARRAY',
                    8: 'DATETIME',
                    9: 'TEXT',
                    10: 'DATE',
                    11: 'TIME',
                    12: 'BOOLEAN',
                    13: 'BOOLEAN',
                    14: 'TIME_TZ',
                    15: 'OBJECT_INSTANT',
                    16: 'TIMESTAMP_TZ_UTC',
                    17: 'TIMESTAMP_LTZ_UTC',
                    18: 'TIME_LTZ',
                    19: 'TIME_NTZ',
                    20: 'TIME_TZ_UTC',
                    21: 'TIMESTAMP_NTZ_UTC',
                    22: 'TIMESTAMP_LTZ_UTC',
                    23: 'TIMESTAMP_TZ_UTC',
                    24: 'VARIANT_OBJECT',
                    25: 'TIMESTAMP_TZ_FIXED',
                    26: 'TIMESTAMP_LTZ_FIXED',
                    27: 'TIME_TZ_FIXED',
                    28: 'TIME_LTZ_FIXED',
                    29: 'TIME_NTZ_FIXED',
                }

                # Convert numeric data types to string representation
                data_types_str = [snowflake_default_type_code.get(code, str(code)) for code in data_type_code]

                columns_info = [{'label': col, 'datatype': data_types_str[i]} for i, col in enumerate(columns)]
                
                results = cursor.fetchall()

                # Convert results to key-value pairs
                data = [dict(zip(columns, row)) for row in results]
                
                response_data = [{'column_data': {"column": columns, "type": data_types_str} , 'data': data, "columns": columns_info}]

                cursor.close()

                connection.close()

                return Response(response_data, status=status.HTTP_200_OK)

            else:

                return Response({'error': "Query can't be blank"}, status=status.HTTP_400_BAD_REQUEST)

        except snowflake.connector.errors.ProgrammingError as e:
            # Handle Snowflake ProgrammingError
            error_message = f"Snowflake ProgrammingError: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

        except snowflake.connector.errors.DatabaseError as e:
            # Handle Snowflake DatabaseError
            error_message = f"Snowflake DatabaseError: {str(e)}"
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

    else:

        return Response({"error": "Database not Found"}, status=status.HTTP_400_BAD_REQUEST)



# def fn_ins_upd_column_data(tabl_col_data, tableListData, def_query_id, created_by_id, last_updated_by_id):

#     columnListId = []

#     for column_data in tabl_col_data["Page4"]["getSelectedColumn"]:
#         for col_single_data in column_data["table_columns"]:

#             col_alias_name = find_column_alias(
#                 tabl_col_data["Page4"]["getcolumnalias"], column_data["table_name"], col_single_data["columnName"])

#             tbl_id = find_table(tableListData, column_data["table_name"])

#             if col_alias_name is not None:
#                 postColumnData = {
#                     "table_column_query_id": def_query_id,
#                     "column_name": col_single_data["columnName"],
#                     "table_column_table_id": tbl_id,
#                     "alias_name": col_alias_name["setAliasName"],
#                     "col_function": col_alias_name["setColumnFunction"],
#                     "created_by": created_by_id,
#                     "last_updated_by": last_updated_by_id
#                 }

#                 if "id" in col_single_data:
#                     columnTable = query_builder_table_columns.objects.get(
#                         id=col_single_data["id"])
#                     queryColumnserilizer = qb_table_columns_serializers(
#                         instance=columnTable, data=postColumnData)

#                     if (queryColumnserilizer.is_valid()):
#                         queryColumnserilizer.save()
#                         columnListId.append(
#                             {'id': queryColumnserilizer.data["id"], "column_name": queryColumnserilizer.data["column_name"]})

#                 else:
#                     queryColumnserilizer = qb_table_columns_serializers(
#                         data=postColumnData)
#                     if (queryColumnserilizer.is_valid()):
#                         queryColumnserilizer.save()
#                         columnListId.append(
#                             {'id': queryColumnserilizer.data["id"], "column_name": queryColumnserilizer.data["column_name"]})

#             else:
#                 postColumnData = {
#                     "table_column_query_id": def_query_id,
#                     "column_name": col_single_data["columnName"],
#                     "table_column_table_id": tbl_id,
#                     "alias_name": None,
#                     "col_function": None,
#                     "created_by": created_by_id,
#                     "last_updated_by": last_updated_by_id
#                 }

#                 if "id" in col_single_data:
#                     columnTable = query_builder_table_columns.objects.get(
#                         id=col_single_data["id"])
#                     queryColumnserilizer = qb_table_columns_serializers(
#                         instance=columnTable, data=postColumnData)

#                     if (queryColumnserilizer.is_valid()):
#                         queryColumnserilizer.save()
#                         columnListId.append(
#                             {'id': queryColumnserilizer.data["id"], "column_name": queryColumnserilizer.data["column_name"]})

def find_table(tableList, table_name):
    for tabledata in tableList:
        if tabledata['tb_name'] == table_name:
            return tabledata['id']

def find_column_alias(aliasList, table_name, colName):
    if len(aliasList) != 0:
        for alias in aliasList:
            if (alias['selectedColumnName'] == colName) and (alias['selectedTableName'] == table_name):
                return str(alias['setAliasName'])

def fn_ins_upd_column_selection(data,table_name,table_id,def_query_id,created_by, last_updated_by):
    Column_sel = data['Page3'] if "Page3" in data else []
    Alias_data = data['Page4']['getcolumnalias'] if "Page4" in data else []
    Aggregation_data = data['Page5'] if "Page5" in data else []
    if "Page3" in data:
        if len(Column_sel) > 0:
            for column_data in Column_sel:
                if column_data['table_name'] == table_name:
                    postColumnData={
                        "column_name": column_data["column"]["columnName"],
                        "column_data_type": column_data["column"]["dataType"],
                        "alias_name": find_column_alias(Alias_data, table_name, column_data["column"]["columnName"]) if len(Alias_data)>=0 else '',
                        "table_column_query_id": def_query_id,
                        "table_column_table_id": table_id,
                        "created_by":created_by,
                        "last_updated_by": last_updated_by
                    }
                    if 'id' in column_data["column"]:
                        columnTable = query_builder_table_columns.objects.get(id = column_data["column"]["id"])
                        queryColumnserilizer = qb_table_columns_serializers(instance = columnTable,data =postColumnData )
                        
                        if queryColumnserilizer.is_valid():
                            queryColumnserilizer.save() 
                            fn_ins_upd_aggreation_data(Aggregation_data,table_name, column_data["column"]["columnName"],column_data["column"]["id"],table_id,def_query_id,created_by, last_updated_by)
                    else:
                        queryColumnserilizer = qb_table_columns_serializers(data =postColumnData )          
                        if queryColumnserilizer.is_valid():
                            queryColumnserilizer.save()
                            fn_ins_upd_aggreation_data(Aggregation_data,table_name, column_data["column"]["columnName"],queryColumnserilizer.data['id'],table_id,def_query_id,created_by, last_updated_by)
                        else:
                            print(queryColumnserilizer.errors)
                            return Response("Column Selection and Alias Setup page not saved...", status=status.HTTP_400_BAD_REQUEST)
                # for column_data in tabl_col_data["Page4"]["getSelectedColumn"]:
                #     for col_single_data in column_data["table_columns"]:
                        
                #         col_alias_name = find_column_alias(tabl_col_data["Page4"]["getcolumnalias"],column_data["table_name"],col_single_data["columnName"]) 
                        
                #         tbl_id= find_table(tableListData,column_data["table_name"])
                        
                #         if col_alias_name is not None:
                            
                            # postColumnData={
                            #     "table_column_query_id": def_query_id,
                            #     "column_name": col_single_data["columnName"],
                            #     "table_column_table_id": tbl_id,
                            #     "alias_name": col_alias_name["setAliasName"],
                            #     "col_function":col_alias_name["setColumnFunction"],
                            #     "created_by":created_by_id,
                            #     "last_updated_by": last_updated_by_id
                            # }
                            
                            
                #             if "id" in col_single_data:
                                
                                # columnTable = query_builder_table_columns.objects.get(id = col_single_data["id"])
                                # queryColumnserilizer = qb_table_columns_serializers(instance = columnTable,data =postColumnData )
                                
                                # if (queryColumnserilizer.is_valid()):
                                #         queryColumnserilizer.save() 
                #                         columnListId.append({'id':queryColumnserilizer.data["id"],"column_name":queryColumnserilizer.data["column_name"]})
                                
                #             else:
                                
                #                 queryColumnserilizer = qb_table_columns_serializers(data = postColumnData)
                #                 if (queryColumnserilizer.is_valid()):
                #                     queryColumnserilizer.save()
                #                     columnListId.append({'id':queryColumnserilizer.data["id"],"column_name":queryColumnserilizer.data["column_name"]})
                                
                #         else:
                #             postColumnData={
                #                 "table_column_query_id": def_query_id,
                #                 "column_name": col_single_data["columnName"],
                #                 "table_column_table_id": tbl_id,
                #                 "alias_name": None,
                #                 "col_function":None,
                #                 "created_by":created_by_id,
                #                 "last_updated_by": last_updated_by_id
                #             }
                            
                #             if "id" in col_single_data:
                                
                #                 columnTable = query_builder_table_columns.objects.get(id = col_single_data["id"])
                #                 queryColumnserilizer = qb_table_columns_serializers(instance = columnTable,data =postColumnData )
                                
                #                 if (queryColumnserilizer.is_valid()):
                #                     queryColumnserilizer.save()
                #                     columnListId.append({'id':queryColumnserilizer.data["id"],"column_name":queryColumnserilizer.data["column_name"]})
                                
                #             else:
                                
                #                 queryColumnserilizer = qb_table_columns_serializers(data = postColumnData)
                #                 if (queryColumnserilizer.is_valid()):
                #                     queryColumnserilizer.save()
                #                     columnListId.append({'id':queryColumnserilizer.data["id"],"column_name":queryColumnserilizer.data["column_name"]})
                                    
                
                # fn_ins_upd_aggreation_data(tabl_col_data,columnListId,tbl_id,def_query_id,created_by_id, last_updated_by_id,tableListData)


def fn_ins_upd_aggreation_data(data,table_name,column_name,column_id,table_id,def_query_id,created_by, last_updated_by):
    if len(data) > 0:
        for aggregatedColumnData in data:
            if aggregatedColumnData['selectedColumn'] == column_name and aggregatedColumnData['selectedTable'] == table_name:

                listofaggregatetabledata = {
                    "agg_fun_name": aggregatedColumnData["selectedAttribute"],
                    "table_aggragate_query_id": def_query_id,
                    "table_aggregate_table_id": table_id,
                    "table_aggregate_column_id": column_id,
                    "created_by": created_by,
                    "last_updated_by": last_updated_by
                }

                if "id" in aggregatedColumnData:
                    aggregateData = query_builder_aggeration_function_table.objects.get(id= aggregatedColumnData["id"])
                    queryAggregateserilizer = qb_table_aggergate_serializers(instance= aggregateData,data=listofaggregatetabledata)
                    
                    if queryAggregateserilizer.is_valid():
                        queryAggregateserilizer.save()
                    else:
                        print(queryAggregateserilizer.errors)
                        return Response("Query definition page not saved...", status=status.HTTP_400_BAD_REQUEST)
                else:
                    queryAggregateserilizer = qb_table_aggergate_serializers(data= listofaggregatetabledata)
                    if queryAggregateserilizer.is_valid():
                        queryAggregateserilizer.save()
                    else:
                        print(queryAggregateserilizer.errors)
                        return Response("Query definition page not saved...", status=status.HTTP_400_BAD_REQUEST)

    # fn_ins_upd_join_data(agg_col_data, tbl_id, def_query_id, created_by_id, last_updated_by_id, tableListData)


def find_table_id(data, table_name):
    for tabledata in data:
        if tabledata['table_name'] == table_name:
            return tabledata['table_id']

def fn_ins_upd_join_data(data, table_data, def_query_id, created_by, last_updated_by):
    if "Page6" in data:
        Join_data = data["Page6"]["getjoinrows"]
        if len(Join_data) > 0:
            for jointableData in Join_data:
                listofjointabledata = {
                    "join_column_name1": jointableData["selectedColumn"],
                    "join_column_name2": jointableData["selectedColumn2"],
                    "join_type": jointableData["selectedAttribute"],
                    "tab_join_table_id_one": find_table_id(table_data, jointableData["selectedTable"]),
                    "tab_join_table_id_two": find_table_id(table_data, jointableData["selectedTable2"]),
                    "tab_join_query_id": def_query_id,
                    "created_by": created_by,
                    "last_updated_by": last_updated_by
                }

                if "id" in jointableData:
                    joinTableData = query_builder_table_joins.objects.get(id=jointableData["id"])
                    joinTableDataSerializers = qb_table_joins_serializers(instance=joinTableData, data=listofjointabledata)

                    if joinTableDataSerializers.is_valid():
                        joinTableDataSerializers.save()
                    else:
                        print(joinTableDataSerializers.errors)
                        return Response("Table join data not saved...", status=status.HTTP_400_BAD_REQUEST)
                else:
                    joinTableDataSerializers = qb_table_joins_serializers(data=listofjointabledata)
                    if joinTableDataSerializers.is_valid():
                        joinTableDataSerializers.save()
                    else:
                        print(joinTableDataSerializers.errors)
                        return Response("Table join data not saved...", status=status.HTTP_400_BAD_REQUEST)
            fn_ins_upd_column_filter_data(data, table_data, def_query_id, created_by, last_updated_by)
            

# def fn_ins_upd_join_data(data, table_data, def_query_id, created_by, last_updated_by):
#     Join_data = data["Page6"]["getjoinrows"]
#     if len(Join_data) > 0:
#         for jointableData in Join_data:
#             listofjointabledata = {
#                 "join_column_name1": jointableData["selectedColumn"],
#                 "join_column_name2": jointableData["selectedColumn2"],
#                 "join_type": jointableData["selectedAttribute"],
#                 "tab_join_table_id_one": find_table_id(table_data, jointableData["selectedTable"]),
#                 "tab_join_table_id_two": find_table_id(table_data, jointableData["selectedTable2"]),
#                 "tab_join_query_id": def_query_id,
#                 "created_by": created_by,
#                 "last_updated_by": last_updated_by
#             }

#             if "id" in jointableData:
#                 print("it have id")
#             #     joinTableData = query_builder_table_joins.objects.get(
#             #         id=jointableData["id"])
#             #     joinTableDataSerializers = qb_table_joins_serializers(
#             #         instance=joinTableData, data=listofjointabledata)

#             #     if joinTableDataSerializers.is_valid():
#             #         joinTableDataSerializers.save()
#             else:
#                 joinTableDataSerializers = qb_table_joins_serializers(data=listofjointabledata)
#                 if joinTableDataSerializers.is_valid():
#                     joinTableDataSerializers.save()
#                 else:
#                     print(queryDefnitionSerilazier.errors)
#                     return Response("Table join data not saved...", status=status.HTTP_400_BAD_REQUEST)
   

def fn_ins_upd_column_filter_data(data, table_data, def_query_id, created_by, last_updated_by):
    if 'Page7' in data:
        Column_sel = data['Page7']
        if len(Column_sel) > 0:
            for columnfilterdata in Column_sel:
                listfiltercolumndata = {
                    "column_name": columnfilterdata["column_name"],
                    "column_filter": columnfilterdata["operator"],
                    "column_value": columnfilterdata["value"],
                    # "column_value": f"{columnfilterdata[i]['start_value']},{columnfilterdata[i]['end_value']}",
                    "tab_filter_query_id": def_query_id,
                    "tab_filter_tale_id": find_table_id(table_data, columnfilterdata["table_name"]),
                    "created_by": created_by,
                    "last_updated_by": last_updated_by
                }
                if 'id' in columnfilterdata:
                    existTableFilter =query_builder_table_column_filter.objects.get(id=columnfilterdata["id"])
                    columnfilterserializer = qb_table_column_filter_serializers(instance=existTableFilter, data=listfiltercolumndata)
                    if columnfilterserializer.is_valid():
                        columnfilterserializer.save()
                    else:
                        print("columnfilterserializer.errors", columnfilterserializer.errors)
                        return Response("Column Filter page data is not saved...", status=status.HTTP_400_BAD_REQUEST)
                else:
                    columnfilterserializer = qb_table_column_filter_serializers(data=listfiltercolumndata)
                    if columnfilterserializer.is_valid():
                        columnfilterserializer.save()
                    else:
                        print("columnfilterserializer.errors", columnfilterserializer.errors)
                        return Response("Column Filter page data is not saved...", status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response("Column Filter page data undefined...", status=status.HTTP_400_BAD_REQUEST)
    # return Response(columnfilterserializer.data, status=status.HTTP_200_OK)

@api_view(["PUT"])
def fn_ins_query_column_data(request):

    requestQueryData = request.data
    
    
    connection_info = requestQueryData["Page1"]["savedConnectionItems"]

    connection_query_name = requestQueryData["Page1"]["query_name"]

    # postConnData = {
    #     "query_name": connection_query_name,
    #     "connection_id": connection_info["id"],
    #     "query_text": connection_info["connection_name"],
    #     "created_by": connection_info["created_by"],
    #     "last_updated_by": connection_info["last_updated_by"]
    # }

    postConnData = {
        "query_name": connection_query_name,
        "connection_id": connection_info["id"],
        "query_text": connection_info["connection_name"],
        "query_status": False,
        "query_type": False,
        "created_user": requestQueryData["Page1"]["created_user"],
        "created_by": connection_info["created_by"],
        "last_updated_by": connection_info["last_updated_by"]
    }

    if "id" in requestQueryData["Page1"]:
        dataDefinitionTable = query_definition.objects.get(
            id=requestQueryData["Page1"]["id"])
        queryDefnitionSerilazier = qb_defnition_serializer(
            instance=dataDefinitionTable, data=postConnData)

        if queryDefnitionSerilazier.is_valid():
            queryDefnitionSerilazier.save()
            fun_ins_upd_builder_table(
                requestQueryData, queryDefnitionSerilazier.data["id"], connection_info["created_by"], connection_info["last_updated_by"])

    else:
        queryDefnitionSerilazier = qb_defnition_serializer(data=postConnData)
        if queryDefnitionSerilazier.is_valid():
            queryDefnitionSerilazier.save()
            fun_ins_upd_builder_table(
                requestQueryData, queryDefnitionSerilazier.data["id"], connection_info["created_by"], connection_info["last_updated_by"])
            return Response(requestQueryData, status=status.HTTP_200_OK)
            # return Response(requestQueryData,status = status.HTTP_201_CREATED)
    
    return Response(queryDefnitionSerilazier,status=status.HTTP_200_OK)
    
    

# def get_alias_name()



def findColumnId(requestAggregateData, column_id):
    for columnName in column_id:
        if columnName["column_name"] == requestAggregateData:
            return columnName["id"]

def fun_ins_upd_builder_table(data, def_query_id, created_by, last_updated_by):
    Table_sel = data['Page2']
    for table_data in Table_sel:                 
        postTableData = {
            "table_name": table_data["table_name"],
            "table_id": table_data["table_id"],
            "query_id": def_query_id,
            "created_by": created_by,
            "last_updated_by": last_updated_by
        }
        if "id" in table_data and "query_id" in table_data:
            print("table data have id")
            # dataTable = query_builder_table.objects.get(id = table_data["id"],query_id = table_data["query_id"])
            # querytableserilizer = qb_table_serializer(instance=dataTable, data=postTableData)

            # postTableData = {
            #     "table_name": table_data["table_name"],
            #     "table_id": table_data["table_id"],
            #     "query_id": def_query_id,
            #     "created_by": created_by_id,
            #     "last_updated_by": last_updated_by_id
            # }

            # if "id" in table_data and "query_id" in table_data["query_id"]:
            #     dataTable = query_builder_table.objects.get(
            #         id=table_data["id"], query_id=table_data["query_id"])
            #     querytableserilizer = qb_table_serializer(
            #         instance=dataTable, data=postTableData)

            #     if querytableserilizer.is_valid():
            #         querytableserilizer.save()
            #         tableListData.append(
            #             {'id': querytableserilizer.data["id"], 'tb_name': querytableserilizer.data["table_name"]})
            #     else:
            #         return Response(querytableserilizer.errors, "err:", status=status.HTTP_400_BAD_REQUEST)
        else:
            querytableserilizer = qb_table_serializer(data=postTableData)
            if querytableserilizer.is_valid():
                querytableserilizer.save()
                fn_ins_upd_column_data(data, querytableserilizer.data['id'], def_query_id,created_by, last_updated_by)
            else:
                print(queryDefnitionSerilazier.errors)
                return Response("Table Selection page not saved...", status=status.HTTP_400_BAD_REQUEST)

def fun_ins_upd_table_selection(data, def_query_id, created_by, last_updated_by, allResponseData):
    if "Page2" in data:
        Table_sel = data['Page2']
        savedtableIddata = []
        ResponseData = []
        for table_data in Table_sel:                 
            postTableData = {
                "table_name": table_data["table_name"],
                "table_id": table_data["table_id"],
                "query_id": def_query_id,
                "created_by": created_by,
                "last_updated_by": last_updated_by
            }
            if "id" in table_data:
                print("table data have id")
                dataTable = query_builder_table.objects.get(id = table_data["id"],query_id = def_query_id)
                querytableserilizer = qb_table_serializer(instance=dataTable, data=postTableData)
                if querytableserilizer.is_valid():
                    querytableserilizer.save()
                    savedtableIddata.append({
                        'table_id': table_data["id"], 
                        'table_name': table_data["table_name"]
                        })
                    fn_ins_upd_column_selection(data,table_data["table_name"],table_data['id'], def_query_id,created_by, last_updated_by)
                else:
                    print(querytableserilizer.errors)
                    return Response("Table Selection page not saved...", status=status.HTTP_400_BAD_REQUEST)
            else:
                querytableserilizer = qb_table_serializer(data=postTableData)
                if querytableserilizer.is_valid():
                    querytableserilizer.save()
                    # ResponseData.append(querytableserilizer.data)
                    savedtableIddata.append({
                        'table_id': querytableserilizer.data["id"], 
                        'table_name': querytableserilizer.data["table_name"]
                        })
                    fn_ins_upd_column_selection(data,table_data["table_name"], querytableserilizer.data['id'], def_query_id,created_by, last_updated_by)
                else:
                    print(querytableserilizer.errors)
                    return Response("Table Selection page not saved...", status=status.HTTP_400_BAD_REQUEST)
        # allResponseData['Page2'] = ResponseData
        fn_ins_upd_join_data(data,savedtableIddata, def_query_id,created_by,last_updated_by)



@api_view(['POST'])
def ins_and_upd_connection_data(request):
    connectionData = request.data
    allResponseData = []
    if len(connectionData) > 0:
        Query_def = connectionData["Page1"]
        query_definition_data = {
            "query_name": Query_def['query_name'],
            "connection_id": Query_def["savedConnectionItems"]["id"],
            "query_text": Query_def["query_text"] if "query_text" in Query_def else '',
            "query_status": True if "query_text" in Query_def else False,
            "query_type": False,
            "created_user": Query_def["created_user"],
            "created_by": Query_def["created_by"],
            "last_updated_by": Query_def["last_updated_by"]
        }

        if "id" in Query_def:
            print("data have id")
            dataDefinitionTable = query_definition.objects.get(id=Query_def["id"])
            queryDefnitionSerilazier = qb_defnition_serializer(instance=dataDefinitionTable, data=query_definition_data)
            if queryDefnitionSerilazier.is_valid():
                queryDefnitionSerilazier.save()
                print("Query_def Saved....")
                fun_ins_upd_table_selection(connectionData, Query_def["id"], Query_def["created_by"], Query_def["last_updated_by"], allResponseData)
            else:
                print(queryDefnitionSerilazier.errors)
                return Response("Query definition page not saved...", status=status.HTTP_400_BAD_REQUEST)
        else:
            queryDefnitionSerilazier = qb_defnition_serializer(data=query_definition_data)
            if queryDefnitionSerilazier.is_valid():
                queryDefnitionSerilazier.save()
                # allResponseData['Page1'] = queryDefnitionSerilazier.data
                if len(connectionData['Page2']) > 0:
                    fun_ins_upd_table_selection(connectionData, queryDefnitionSerilazier.data["id"], Query_def["created_by"], Query_def["last_updated_by"], allResponseData)
                    # fn_ins_upd_join_data(connectionData,connectionData['Page2'], queryDefnitionSerilazier.data["id"], Query_def["created_by"], Query_def["last_updated_by"])
            else:
                print(queryDefnitionSerilazier.errors)
                return Response("Query definition page not saved...", status=status.HTTP_400_BAD_REQUEST)

        return Response("Success", status=status.HTTP_200_OK)
    else:
        return Response("failed", status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
def load_data(request):
    data = request.data['etldata']
    params = request.data['params']
    function = request.data['function']

    df = pd.DataFrame(data)

    if function == 'Find and Replace':
        replace_res = df[params['column']].replace(params['find'], params['replace'], inplace=True)
        df2= df.to_dict(orient ='records')
        return Response(df2, status=status.HTTP_200_OK)
    elif function == 'Merge Columns':
        df[params['columnname']] = df[params['column1']] + str(params['split']) + df[params['column2']]
        df2= df.to_dict(orient ='records')
        return Response(df2, status=status.HTTP_200_OK)
    
    return Response("Failed", status=status.HTTP_400_BAD_REQUEST)
    
    
    

@api_view(["POST"])
def fn_data_to_transform(request):
    rowData = request.data
        
    dataframeData = rowData["data"]
    
    method = rowData["method"]
    
    df = pd.DataFrame(dataframeData)
    
    # to selected remove columns
    if method == 'Remove Columns':
        print('Remove Columns')
        selectColumn = rowData["selected_column"]
        
        columnDrop = df.drop(columns=selectColumn)
        
        data_list = columnDrop.to_dict(orient='records')
            
        return Response(data_list,status=status.HTTP_200_OK)
    
    # to split the selected column with the delimiter
    elif method == 'Split':
        
        delimiter = rowData["delimiter"]
        selectColumn = rowData["selected_column"]
        df[selectColumn] = df[selectColumn].str.split(delimiter)
        result_data_list = df.to_dict(orient="records")
        return Response(result_data_list,status=status.HTTP_200_OK)
    
    # to remove the dulicates from the request data
    elif method == 'Duplicates':
        
        duplicateDrop = df.drop_duplicates()
        duplicate_list = duplicateDrop.to_dict(orient='records')
        removed_duplicates = len(df)-len(duplicateDrop)
        return Response({'duplicate_list': duplicate_list,'removed_duplicates_count': removed_duplicates},status=status.HTTP_200_OK)
    
    # to drop the null data
    elif method == 'Sort':
        selectColumn = rowData["selected_column"]
        sortdata = df.sort_values(by=selectColumn)
        result_sortvalues = sortdata.to_dict(orient='records')
        return Response(result_sortvalues,status=status.HTTP_200_OK)
    
    # to fill the null values with user input
    elif method == 'FNull':
        fillnullwith = rowData['replacenull']
        fillnadata = df.fillna(fillnullwith)
        result_fillnull = fillnadata.to_dict(orient='records')
        return Response(result_fillnull,status=status.HTTP_200_OK)
        


@api_view(["POST"])
def fn_ins_data_to_source(request):
    requestData = request.data

    dataToInsert = requestData["data"]
    tablenameToInsert = requestData["table_name"]
    connForInsert = requestData["savedConn"]

    if connForInsert['connection_type'] == 'MYSQL':
        
        mydb = sqlConnect.connect(
                    host=connForInsert.get('host_id'),
                    user=connForInsert.get('user_name'),
                    password=connForInsert.get('password'),
                    database=connForInsert.get('database_name'),
                    port=connForInsert.get('port')
                )
        
        with mydb.cursor() as cursor:
            columnName = requestData['data'][0].keys()
            tableName = requestData['table_name']

            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{tableName}'")
            table_exists = cursor.fetchone()

            if not table_exists:
                # Table doesn't exist, create it
                create_table_sql = f"CREATE TABLE {tableName} ({', '.join([f'{column} VARCHAR(255)' for column in columnName])})"
                cursor.execute(create_table_sql)

            # Insert data into the table
            insert_sql = f"INSERT INTO {tableName} ({', '.join(columnName)}) VALUES ({', '.join(['%s']*len(columnName))})"

            for rowData in requestData['data']:
                # Convert date strings to a format acceptable by your database
                values = [
                    rowData[column] if column != 'created_date' and column != 'last_updated_date' else convert_to_database_date(rowData[column])
                    for column in columnName
                ]

                try:
                    cursor.execute(insert_sql, values)
                except Exception as e:
                    print(f"Error inserting data: {e}")

            # Commit changes to the database
            mydb.commit()
        
    elif connForInsert['connection_type'] == 'Snowflake':
        
       connectionStr = snowflake.connector.connect(
            user='REVANRUFUS',
            password='Revan@062797',
            account='vi82049.ap-southeast-1'  
            )
       
       connectionCursor = connectionStr.cursor()
       
       columnName = requestData['data'][0].keys()
       
       tableName = requestData['table_name']
       
       connectionCursor.execute(f"USE DATABASE smpledb")
       
       connectionCursor.execute(f"USE SCHEMA public")  
         
       create_table_sql = f"CREATE TABLE IF NOT EXISTS {tableName} ({', '.join([f'{column} VARCHAR ' for column in columnName])})"
       
       connectionCursor.execute(create_table_sql)
       
       if connectionCursor.rowcount > 0: 
           
            insert_sql = f"INSERT INTO {tableName} ({', '.join([f'{column}' for column in columnName])}) " \
                        f"VALUES ({', '.join(['%s']*len(columnName))})"
                    
            for rowData in requestData['data']:
                    values = tuple(rowData.values())
                    connectionCursor.execute(insert_sql, values)
    

    return Response(requestData, status=status.HTTP_200_OK)

def convert_to_database_date(date_str):
    # Assuming the date format is 'YYYY-MM-DDTHH:MM:SS.SSSSSS'
    datetime_format = '%Y-%m-%dT%H:%M:%S.%f' if '.' in date_str else '%Y-%m-%dT%H:%M:%S'
    return datetime.strptime(date_str, datetime_format).strftime('%Y-%m-%d %H:%M:%S')

# from functools import cache

@api_view(["POST"])
def dataprofileCompare(request):
    datatocompare = request.data
    
    datasetOne = datatocompare['originalData']
    datasetTwo = json.loads(json.dumps(datatocompare['transformedData']).replace('"NaN"', 'null'))
    
    
    dfOne = pd.DataFrame(datasetOne['data'])
    dfTwo = pd.DataFrame(datasetTwo)
    
    
    
    profileReportOne = ProfileReport(dfOne,title="Original Data",minimal=True)
    
    profileReportTwo = ProfileReport(dfTwo,title="Transformed Data",minimal=True)
    
    comparison_Report = profileReportOne.compare(profileReportTwo)
    dataProfiler=comparison_Report.to_html()

    return HttpResponse(dataProfiler, content_type='text/html')



@api_view(["POST"])
def fn_data_quality(request):
    
    requestQualityData = request.data
    
    columnHeaders = requestQualityData['columns']  
      
    df = pd.DataFrame(requestQualityData['data'], columns=[column['label'] for column in columnHeaders])

    
    response_data = []
    
    for columnquality in columnHeaders:
        
        column_data = df[columnquality['label']]
        
        total = len(column_data)
        not_null_col = column_data.count()
        null_count_column = column_data.isnull().sum()
        blank_count = (column_data == '').sum()
        distinct_val = column_data.nunique()
        max_length = column_data.astype(str).apply(lambda x: len(x)).max()
        min_length = column_data.astype(str).apply(lambda x: len(x)).min() 
                
        if pd.api.types.is_numeric_dtype(column_data):
            column_data = pd.to_numeric(column_data, errors='coerce')
            column_data = column_data.dropna()  # Drop non-numeric values
            
            quantiles = column_data.quantile([0.25, 0.5, 0.75])
            q1 = quantiles[0.25]
            q2 = quantiles[0.75]
            iqr = q2 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q2 + 1.5 * iqr

            outliers_numeric = (column_data < lower_bound) | (column_data > upper_bound)
            outliers = int(outliers_numeric.any())
            
            max_value = column_data.max()
            min_value = column_data.min()
        else:
            outliers = 0
        
        numeric_count = column_data.apply(lambda x: isinstance(x, (int, float, np.number))).sum()
        alphabet_only_values = column_data.astype(str).str.count(r'^[a-zA-Z]+$').sum()
        alphanumeric_only_values = column_data.astype(str).str.isalnum().sum()
        contains_special_char_count = total - column_data.astype(str).str.isalnum().sum()
        
        top_ten_distinct_values = column_data.unique()[:10]
        top_ten_distributed_values = column_data.value_counts().nlargest(10)
        
        duplicate_values = total - distinct_val
        
        response_data.append({
            'QUERY_ID': requestQualityData['id'],
            'QUERY_NAME': requestQualityData['query_name'],
            'COLUMN_NAME': columnquality['label'],
            'COLUMN_DATATYPE': columnquality['datatype'],
            'TOTAL_COUNT': total,
            'NOT_NULL_COUNT': not_null_col,
            'NULL_COUNT': null_count_column,
            'BLANK_COUNT': blank_count,
            'DISTINCT_VALUES_COUNT': distinct_val,
            'MAX_LENGTH': max_length,
            'MIN_LENGTH': min_length,
            'MAX_VALUE': max_value,
            'MIN_VALUE': min_value,
            'NUMERIC_ONLY_VALUES_COUNT': numeric_count,
            'ALPHABETS_ONLY_VALUES_COUNT': alphabet_only_values,
            'ALPHANUMERIC_ONLY_VALUES_COUNT': alphanumeric_only_values,
            'CONTAINS_SPECIAL_CHAR_COUNT': contains_special_char_count,
            'TOP_TEN_DISTINCT_VALUES': top_ten_distinct_values,
            'TOP_TEN_DISTRIBUTED_VALUES': top_ten_distributed_values,
            'DUPLICATE': duplicate_values,
            'OUTLIERS': outliers
        })
                
    return Response(response_data, status=status.HTTP_200_OK)



@api_view(['POST'])
def ins_data_quality_metrics(request):
    profilerDataRequest = request.data
    
    
    saved_data_list = []
    
    for profilerData in profilerDataRequest:
        
        top_ten_values = profilerData.get('TOP_TEN_DISTINCT_VALUES', []) 
        top_ten_values_str = ",".join(str(value) for value in top_ten_values)
        
        top_ten_distributed_values = profilerData.get('TOP_TEN_DISTRIBUTED_VALUES', [])
        top_ten_distributed_values_str = ",".join(map(str, top_ten_distributed_values))
        
        dictofProfilerData = {
            'QUERY_ID':profilerData['QUERY_ID'],
            'QUERY_NAME':profilerData['QUERY_NAME'],
            'COLUMN_NAME':profilerData['COLUMN_NAME'],
            'COLUMN_DATATYPE':profilerData['COLUMN_DATATYPE'],
            'TOTAL_COUNT':profilerData['TOTAL_COUNT'],
            'NOT_NULL_COUNT':profilerData['NOT_NULL_COUNT'],
            'NULL_COUNT':profilerData['NULL_COUNT'],
            'BLANK_COUNT':profilerData['BLANK_COUNT'],
            'DISTINCT_VALUES_COUNT':profilerData['DISTINCT_VALUES_COUNT'],
            'MAX_LENGTH':profilerData['MAX_LENGTH'],
            'MIN_LENGTH':profilerData['MIN_LENGTH'],
            'MAX_VALUE':profilerData['MAX_VALUE'],
            'MIN_VALUE':profilerData['MIN_VALUE'],
            'NUMERIC_ONLY_VALUES_COUNT':profilerData['NUMERIC_ONLY_VALUES_COUNT'],
            'ALPHABETS_ONLY_VALUES_COUNT':profilerData['ALPHABETS_ONLY_VALUES_COUNT'],
            'ALPHANUMERIC_ONLY_VALUES_COUNT':profilerData['ALPHANUMERIC_ONLY_VALUES_COUNT'],
            'CONTAINS_SPECIAL_CHAR_COUNT':profilerData['CONTAINS_SPECIAL_CHAR_COUNT'],
            'TOP_TEN_DISTINCT_VALUES':top_ten_values_str,
            'TOP_TEN_DISTRIBUTED_VALUES':top_ten_distributed_values_str,
            'DUPLICATE':profilerData['DUPLICATE'],
            'OUTLIERS':profilerData['OUTLIERS']
        }
        
        
        
        profilerserializers = metrics_serilizer(data = dictofProfilerData)
        
        
        if profilerserializers.is_valid():
            saved_instance = profilerserializers.save()
            saved_data_list.append(metrics_serilizer(saved_instance).data)
        else:
            print(profilerserializers.errors)

    return Response(saved_data_list,status=status.HTTP_200_OK)

    

@api_view(['GET'])
def get_metrics_data(request, id=0):
    try:
        if id == 0:
            return Response({"msg": "No Data Present"}, status=status.HTTP_404_NOT_FOUND)
        else:
            MetricsData = metrics.objects.filter(
                QUERY_ID=id)
            
            metricsSerilizer = metrics_serilizer(
                MetricsData, many=True)
            
            if (len(metricsSerilizer.data) > 0):
                framedata = pd.DataFrame(metricsSerilizer.data)
                framedata['RUN_DATE'] = pd.to_datetime(framedata['RUN_DATE'])
                recent_dates_table = framedata["RUN_DATE"].value_counts().head(5).index.tolist()
                datetime_values_table = [pd.to_datetime(ts).strftime('%Y-%m-%d %H:%M') for ts in recent_dates_table]
                framedata['RUN_DATE_truncated'] = framedata['RUN_DATE'].dt.strftime('%Y-%m-%d %H:%M')
                Changedframedata = framedata[framedata['RUN_DATE_truncated'].isin(datetime_values_table)]

                return Response(Changedframedata.to_dict(orient="records"), status=status.HTTP_200_OK)
            else:
                return Response({"msg": "No Data Present"}, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as exc:
        print(f"==>> exc: {exc}")
        return Response({"msg": exc}, status=status.HTTP_404_NOT_FOUND)
    
# API Insert for meta_metrics Table
@api_view(['POST'])
def ins_data_quality_meta_metrics(request):
    profilerDataRequest = request.data

    analysis = profilerDataRequest.get('analysis')
    table_data = profilerDataRequest.get('table')
    table_categorical_data = table_data.get('types')
    column_analysis = profilerDataRequest.get('variables')

    saved_data_list = []

        
    for columns in column_analysis:
        
        MIN_TEN_VALUES_LIST = list(column_analysis[columns].get('value_counts_index_sorted', {}).keys())[:10]
        MIN_TEN_VALUES = ",".join(str(value) for value in MIN_TEN_VALUES_LIST)
        
        MAX_TEN_VALUES_LIST = list(column_analysis[columns].get('value_counts_index_sorted', {}).keys())[-10:]
        MAX_TEN_VALUES = ",".join(map(str, MAX_TEN_VALUES_LIST))
        
        dictofProfilerData = {
            # Table Level Common Fields
            'TABLE_NAME' : analysis["title"],
            'ANALYSIS_START' : analysis['date_start'],
            'ANALYSIS_END' : analysis['date_end'],

            'ROW_COUNT' : table_data['n'],
            'COLUMN_COUNT' : table_data['n_var'],
            'MEMORY_SIZE' : table_data['memory_size'],
            'RECORD_SIZE' : table_data['record_size'],
            'MISSING_CELL_COUNT' : table_data['n_cells_missing'],
            'MISSING_COL_COUNT' : table_data['n_vars_with_missing'],
            'MISSING_PERCENT' : table_data['p_cells_missing'],
            'NUMERIC_COL_COUNT' : table_categorical_data.get('Numeric') if table_categorical_data.get('Numeric') else 0,
            'DATETIME_COL_COUNT' : table_categorical_data.get('DateTime') if table_categorical_data.get('DateTime') else 0,
            'CATEGORICAL_COL_COUNT' : table_categorical_data.get('Categorical') if table_categorical_data.get('Categorical') else 0,
            'TEXT_COL_COUNT' : table_categorical_data.get('Text') if table_categorical_data.get('Text') else 0,

            # COLUMN LEVEL COMMON FIELDS
            'COLUMN_NAME' : columns,
            'COLUMN_CATEGORY' : column_analysis[columns].get('type'),
            'DISTINCT_COUNT' : column_analysis[columns].get('n_distinct'),
            'DISTINCT_PERCENT' : column_analysis[columns].get('p_distinct'),
            'MISSING_COUNT' : column_analysis[columns].get('n_missing'),
            'MISSING_PERCENT' : column_analysis[columns].get('p_missing'),
            'UNIQUE_COUNT' : column_analysis[columns].get('n_unique'),
            'UNIQUE_PERCENT' : column_analysis[columns].get('p_unique'),
            'MIN_TEN_VALUES' : MIN_TEN_VALUES,
            'MAX_TEN_VALUES' : MAX_TEN_VALUES,
            
                
            # FOR REAL NUMBER AND DATE
            'UNIQUE' : column_analysis[columns].get('is_unique') if column_analysis[columns].get('is_unique') else 0,
            'INFINITE_COUNT' : column_analysis[columns].get('n_infinite') if column_analysis[columns].get('n_infinite') else 0,
            'INFINITE_PERCENT' : column_analysis[columns].get('p_infinite') if column_analysis[columns].get('p_infinite') else 0,
            'MIN_VALUE' : column_analysis[columns].get('min') if column_analysis[columns].get('min') else 0,
            'MAX_VALUE' : column_analysis[columns].get('max') if column_analysis[columns].get('max') else 0,
            'ZERO_COUNT' : column_analysis[columns].get('n_zeros') if column_analysis[columns].get('n_zero') else 0,
            'ZERO_PERCENT' : column_analysis[columns].get('p_zeros') if column_analysis[columns].get('p_zeros') else 0,
            'NEGATIVE_COUNT' : column_analysis[columns].get('n_negative') if column_analysis[columns].get('n_negative') else 0,
            'NEGATIVE_PERCENT' : column_analysis[columns].get('p_negative') if column_analysis[columns].get('p_negative') else 0,
            
            'MEAN' : column_analysis[columns].get('mean') if column_analysis[columns].get('mean') else 0,
            'MEDIAN' : column_analysis[columns].get('median') if column_analysis[columns].get('median') else 0,
            'VARIANCE' : column_analysis[columns].get('variance') if column_analysis[columns].get('variance') else 0,
            'RANGE' : column_analysis[columns].get('range') if column_analysis[columns].get('range') else 0,
            'INTERQUARTILE_RANGE' : column_analysis[columns].get('iqr') if column_analysis[columns].get('iqr') else 0,
            'SUM' : column_analysis[columns].get('sum') if column_analysis[columns].get('sum') else 0,
            'STANDARD_DEVIATION' : column_analysis[columns].get('std') if column_analysis[columns].get('std') else 0,
            'COEFFICIENT_OF_VARIATION' : column_analysis[columns].get('cv') if column_analysis[columns].get('cv') else 0,
            'MEDIAN_ABSOLUTE_DEVIATION' : column_analysis[columns].get('mad') if column_analysis[columns].get('mad') else 0,
            'SKEWNESS' : column_analysis[columns].get('skewness') if column_analysis[columns].get('skewness') else 0,
            'KURTOSIS' : column_analysis[columns].get('kurtosis') if column_analysis[columns].get('kurtosis') else 0,
            'MONOTONICITY' : column_analysis[columns].get('monotonic') if column_analysis[columns].get('monotonic') else 0,
            
        #     # FOR Categorical
            'MAX_LENGTH' : column_analysis[columns].get('max_length') if column_analysis[columns].get('max_length') else 0,
            'MIN_LENGTH' : column_analysis[columns].get('min_length') if column_analysis[columns].get('min_length') else 0,
            'MEAN_LENGTH' : column_analysis[columns].get('mean_length') if column_analysis[columns].get('mean_length') else 0,
            'MEDIAN_LENGTH' : column_analysis[columns].get('median_length') if column_analysis[columns].get('median_length') else 0,
            'TOTAL_CHARACTERS' : column_analysis[columns].get('n_characters') if column_analysis[columns].get('n_characters') else 0,
            'DISTINCT_CHARACTERS' : column_analysis[columns].get('n_characters_distinct') if column_analysis[columns].get('n_characters_distinct') else 0,
            'DISTINCT_CATEGORIES' : column_analysis[columns].get('n_category') if column_analysis[columns].get('n_category') else 0,
            'DISTINCT_SCRIPTS' : column_analysis[columns].get('n_scripts') if column_analysis[columns].get('n_scripts') else 0,
            'DISTINCT_BLOCKS' : column_analysis[columns].get('n_block_alias') if column_analysis[columns].get('n_block_alias') else 0,
        }
        
        profilerserializers = meta_metrics_serilizer(data = dictofProfilerData)

        if profilerserializers.is_valid():
            saved_instance = profilerserializers.save()
            saved_data_list.append(meta_metrics_serilizer(saved_instance).data)
        else:
            print(f"Validation errors for {columns}: {profilerserializers.errors}")
            return Response(profilerserializers.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(saved_data_list,status=status.HTTP_200_OK)