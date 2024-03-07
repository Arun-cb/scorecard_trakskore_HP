
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from django.contrib.auth.models import User
from django.db import IntegrityError
from .serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from datetime import date, timedelta
from django.contrib.auth.models import User, Group
import pandas as pd
from sqlalchemy import create_engine
from django.conf import settings as def_set
from base.api import smtp_mail
import string
import random
import datetime
import os
from rest_framework.exceptions import PermissionDenied
import mysql.connector as sqlConnect
import cx_Oracle
from ydata_profiling import ProfileReport
from ydata_profiling.visualisation.plot import timeseries_heatmap
import snowflake.connector
import time
import json
import math
import numpy as np




@api_view(["PUT"])
def get_ydata_profiling_report(request):
    starttime = time.time()
    connnectionrequestdata = request.data
    saved_connection = connnectionrequestdata["savedConnectionItems"]
    customised_data = connnectionrequestdata["noncustomdata"]
    correlation_data = connnectionrequestdata["customdata"][0]["correlations"]
    time_series_data = connnectionrequestdata["timeseriesdata"]
    date_columns = connnectionrequestdata["date_columns"]
            
    db_type = saved_connection.get("connection_type")

    query = connnectionrequestdata["query_text"]
    query_name = connnectionrequestdata["query_name"]
    
    if db_type == 'MYSQL':

            try:

                query = connnectionrequestdata["query_text"]
                query_name = connnectionrequestdata["query_name"]

                mydb = sqlConnect.connect(
                    host=saved_connection.get("host_id"),
                    user=saved_connection.get("user_name"),
                    password=saved_connection.get("password"),
                    database=saved_connection.get("database_name"),
                )

                mycursor = mydb.cursor(dictionary=True)

                mycursor.execute(query)

                headercolumn = [col[0] for col in mycursor.description]
                
                results = mycursor.fetchall()
                
                mycursor.close()
                
                mydb.close()
                
            except sqlConnect.Error as e:
                # Handle the database-related errors, including syntax errors
                error_message = str(e)

                return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

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

            cursor = connection.cursor()

            cursor.execute(query)
            
            headercolumn= [col[0] for col in cursor.description]
            
            results  = cursor.fetchall()
            
            cursor.close()
            
            connection.close()
            
        except snowflake.connector.errors.ProgrammingError as e:
            # Handle Snowflake ProgrammingError
            error_message = f"Snowflake ProgrammingError: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

        except snowflake.connector.errors.DatabaseError as e:
            # Handle Snowflake DatabaseError
            error_message = f"Snowflake DatabaseError: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

    elif db_type == "Oracle":

        connection_str = f"{saved_connection.get('user_name')}/{saved_connection.get('password')}@{saved_connection.get('host_id')}:{saved_connection.get('port')}/{saved_connection.get('service_name_or_SID')}"
        
        # cursor = None
        # connection = None

        try:

            connection = cx_Oracle.connect(connection_str)
            
            # Create a cursor            
            cursor = connection.cursor()

            # Execute the queries
            cursor.execute(query)

            # Fetch column names from the cursor description
            headercolumn = [col[0] for col in cursor.description]
            
            results = cursor.fetchall()
        
            cursor.close()
            
            connection.close()
            
        except cx_Oracle.Error as e:
                # Handle Oracle errors
            error_message = f"Oracle error: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

    df = pd.DataFrame(results, columns= headercolumn if headercolumn else None)
    
    for i in date_columns:
        df[i] = pd.to_datetime(df[i])

    report = ProfileReport(df, title= query_name,
                dataset={
                    "description": "This profiling report was generated by CITTABASE Solutions Pte. Ltd.",
                    "copyright_holder": "2024 Cittabase Solutions", # © 2024 Copyright Cittabase Solutions
                    # "copyright_year": 2024,
                    "url": "https://www.cittabase.com/",
                },
                interactions={"continuous": False if customised_data[0]["value"] == False else True,"targets": []}, 
                correlations={"auto": {"calculate": True if correlation_data[0]["status"] == True and correlation_data[0]["method"] == "Auto" else False},
                                "pearson": {"calculate": True if correlation_data[1]["status"] == True and correlation_data[1]["method"] == "Pearson" else False},
                                "spearman": {"calculate": True if correlation_data[2]["status"] == True and correlation_data[2]["method"] == "Spearman" else False},
                                "kendall": {"calculate": True if correlation_data[3]["status"] == True and correlation_data[3]["method"] == "Kendall" else False},
                                "phi_k": {"calculate": True if correlation_data[4]["status"] == True and correlation_data[4]["method"] == "Phi K" else False},
                                "cramers": {"calculate": True if correlation_data[5]["status"] == True and correlation_data[5]["method"] == "Cramers" else False}
                            },
                missing_diagrams={
                    "heatmap": True if customised_data[1]["value"] == True else False,
                    "bar": True if customised_data[1]["value"] == True else False,
                    "matrix": True if customised_data[1]["value"] == True else False
                },
                sensitive= False if customised_data[2]["value"] == True else True,
                tsmode= True if time_series_data[0]["value"] == True else False,
                sortby= time_series_data[0]["sort_column"] if time_series_data[0]["sort_column"] else "",
            )
    
    data = report.to_html()
    
    return HttpResponse(data, content_type='text/html')

@api_view(["POST"])
def get_json_report(request):
    starttime = time.time()
    connnectionrequestdata = request.data
    saved_connection = connnectionrequestdata["savedConnectionItems"]
            
    db_type = saved_connection.get("connection_type")

    query = connnectionrequestdata["query_text"]
    query_name = connnectionrequestdata["query_name"]
    date_columns = connnectionrequestdata["date_columns"]
    
    if db_type == 'MYSQL':

            try:

                query = connnectionrequestdata["query_text"]
                query_name = connnectionrequestdata["query_name"]

                mydb = sqlConnect.connect(
                    host=saved_connection.get("host_id"),
                    user=saved_connection.get("user_name"),
                    password=saved_connection.get("password"),
                    database=saved_connection.get("database_name"),
                )

                mycursor = mydb.cursor(dictionary=True)

                mycursor.execute(query)

                headercolumn = [col[0] for col in mycursor.description]
                
                results = mycursor.fetchall()
                
                mycursor.close()
                
                mydb.close()
                
            except sqlConnect.Error as e:
                # Handle the database-related errors, including syntax errors
                error_message = str(e)

                return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

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

            cursor = connection.cursor()

            cursor.execute(query)
            
            headercolumn= [col[0] for col in cursor.description]
            
            results  = cursor.fetchall()
            
            cursor.close()
            
            connection.close()
            
        except snowflake.connector.errors.ProgrammingError as e:
            # Handle Snowflake ProgrammingError
            error_message = f"Snowflake ProgrammingError: {str(e)}"
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

        except snowflake.connector.errors.DatabaseError as e:
            # Handle Snowflake DatabaseError
            error_message = f"Snowflake DatabaseError: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

    elif db_type == "Oracle":

        connection_str = f"{saved_connection.get('user_name')}/{saved_connection.get('password')}@{saved_connection.get('host_id')}:{saved_connection.get('port')}/{saved_connection.get('service_name_or_SID')}"
        
        # cursor = None
        # connection = None

        try:

            connection = cx_Oracle.connect(connection_str)
            
            # Create a cursor            
            cursor = connection.cursor()

            # Execute the queries
            cursor.execute(query)

            # Fetch column names from the cursor description
            headercolumn = [col[0] for col in cursor.description]
            
            results = cursor.fetchall()
        
            cursor.close()
            
            connection.close()
            
        except cx_Oracle.Error as e:
                # Handle Oracle errors
            error_message = f"Oracle error: {str(e)}"
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    df = pd.DataFrame(results, columns= headercolumn if headercolumn else None)

    for i in date_columns:
        df[i] = pd.to_datetime(df[i]) 
    
    report = ProfileReport(df, title= query_name,
        samples=None,
        correlations=None,
        missing_diagrams=None,
        duplicates=None,
        interactions=None)

    json_data = report.to_json()
    
    # Convert JSON string to a Python dictionary
    json_data_1 = json.loads(json_data)

    # Function To Replace NaN to None in Json
    def replace_nan_with_none(obj):
        if isinstance(obj, list):
            return [replace_nan_with_none(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: replace_nan_with_none(value) for key, value in obj.items()}
        elif pd.isna(obj):
            return None
        else:
            return obj
        
    json_data_2 = replace_nan_with_none(json_data_1)
    
    return Response(json_data_2, status=status.HTTP_200_OK)

# ! Test End

@api_view(["PUT"])
def get_data_quality_report(request):
    print("Data Quality Called...")
    starttime = time.time()
    connnectionrequestdata = request.data
    saved_connection = connnectionrequestdata["savedConnectionItems"]
    customised_data = connnectionrequestdata["noncustomdata"]
    correlation_data = connnectionrequestdata["customdata"][0]["correlations"]
    time_series_data = connnectionrequestdata["timeseriesdata"]
            
    db_type = saved_connection.get("connection_type")

    query = connnectionrequestdata["query_text"]
    query_name = connnectionrequestdata["query_name"]
    
    if db_type == 'MYSQL':

        try:

            query = connnectionrequestdata["query_text"]
            query_name = connnectionrequestdata["query_name"]

            mydb = sqlConnect.connect(
                host=saved_connection.get("host_id"),
                user=saved_connection.get("user_name"),
                password=saved_connection.get("password"),
                database=saved_connection.get("database_name"),
            )

            mycursor = mydb.cursor(dictionary=True)

            mycursor.execute(query)

            headercolumn = [col[0] for col in mycursor.description]
            
            results = mycursor.fetchall()
            
            mycursor.close()
            
            mydb.close()
            
        except sqlConnect.Error as e:
            # Handle the database-related errors, including syntax errors
            error_message = str(e)

            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

        finally:
            mycursor.close()
            mydb.close()

    elif db_type == "Snowflake":
        
        # Build the connection string
        connection_str = {
            'user': 'REVANRUFUS',
            'password': 'Revan@062797',
            'account': 'vi82049.ap-southeast-1',
            'warehouse': 'MY_WH',
            'database': 'smpledb',
            'schema': 'public',
            # 'role': saved_connection.get('role'),
        }
        
        try:
            # Attempt to connect to Snowflake
            connection = snowflake.connector.connect(**connection_str)

            cursor = connection.cursor()

            cursor.execute(query)
            
            headercolumn= [col[0] for col in cursor.description]
            
            results  = cursor.fetchall()
            
            cursor.close()
            
            connection.close()
            
        except snowflake.connector.errors.ProgrammingError as e:
            # Handle Snowflake ProgrammingError
            error_message = f"Snowflake ProgrammingError: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

        except snowflake.connector.errors.DatabaseError as e:
            # Handle Snowflake DatabaseError
            error_message = f"Snowflake DatabaseError: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

        finally:
            # Close the cursor and connection in the finally block
            cursor.close()
            connection.close()
    
    elif db_type == "Oracle":

        connection_str = f"{saved_connection.get('user_name')}/{saved_connection.get('password')}@{saved_connection.get('host_id')}:{saved_connection.get('port')}/{saved_connection.get('service_name_or_SID')}"
        
        # cursor = None
        # connection = None

        try:

            connection = cx_Oracle.connect(connection_str)
            
            # Create a cursor            
            cursor = connection.cursor()

            # Execute the queries
            cursor.execute(query)

            # Fetch column names from the cursor description
            headercolumn = [col[0] for col in cursor.description]
            
            results = cursor.fetchall()
        
            cursor.close()
            
            connection.close()
            
        except cx_Oracle.Error as e:
                # Handle Oracle errors
            error_message = f"Oracle error: {str(e)}"
            return HttpResponse(error_message, status=status.HTTP_400_BAD_REQUEST)

        # finally:
        #     # Close the cursor and connection in the finally block
        #     cursor.close()
        #     connection.close()

    df_original = pd.DataFrame(results, columns= headercolumn if headercolumn else None)
    df = df_original.replace('',np.nan,regex = True)
    print("df", df)
    print("-------------------------------------------------")
    print("Table wise Quality")
    # del df['id']
    # df.drop('id', axis=1)
    # print("df", df)
    print("Find dupicate rows ",df.duplicated().tolist().count(True))
    print("-------------------------------------------------")
    print("Column wise Quality")
    for col in headercolumn:
        # z_scores = (df[col] - df[col].mean()) / df[col].std()
        # outliers = df[abs(z_scores) > 3]
        print(col,":")
        print("     Missing_value - ", df[col].isnull().tolist().count(True))
        print("     Dublicated_values - ", df[col].duplicated().tolist().count(True))
        print("     Outliers - ", z_scores)
        print("     ----------      ")
    
    # report = ProfileReport(df, title= query_name,
    #             dataset={
    #                 "description": "This profiling report was generated by CITTABASE Solutions Pte. Ltd.",
    #                 "copyright_holder": "2024 Cittabase Solutions", # © 2024 Copyright Cittabase Solutions
    #                 # "copyright_year": 2024,
    #                 "url": "https://www.cittabase.com/",
    #             },
    #             interactions={"continuous": False if customised_data[0]["value"] == False else True,"targets": []}, 
    #             correlations={"auto": {"calculate": True if correlation_data[0]["status"] == True and correlation_data[0]["method"] == "Auto" else False},
    #                             "pearson": {"calculate": True if correlation_data[1]["status"] == True and correlation_data[1]["method"] == "Pearson" else False},
    #                             "spearman": {"calculate": True if correlation_data[2]["status"] == True and correlation_data[2]["method"] == "Spearman" else False},
    #                             "kendall": {"calculate": True if correlation_data[3]["status"] == True and correlation_data[3]["method"] == "Kendall" else False},
    #                             "phi_k": {"calculate": True if correlation_data[4]["status"] == True and correlation_data[4]["method"] == "Phi K" else False},
    #                             "cramers": {"calculate": True if correlation_data[5]["status"] == True and correlation_data[5]["method"] == "Cramers" else False}
    #                         },
    #             missing_diagrams={
    #                 "heatmap": True if customised_data[1]["value"] == True else False,
    #                 "bar": True if customised_data[1]["value"] == True else False,
    #                 "matrix": True if customised_data[1]["value"] == True else False
    #             },
    #             sensitive= False if customised_data[2]["value"] == True else True,
    #             tsmode= True if time_series_data[0]["value"] == True else False,
    #             # sortby="created_date",
    #             # duplicates=None,
    #         )
    
    # data = report.to_html()
    print(f"Execution Time {time.time()-starttime}")

    return HttpResponse(df, content_type='text/html')


@api_view(["GET"])
def getRoutes(request):
    routes = [
        "/api/token",
        "/api/token/refresh",
    ]

    return Response(routes)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        group = user.groups.filter(user=user).values().first()
        # Add custom claims
        token["username"] = user.username
        token["is_superuser"] = user.is_superuser
        if token["is_superuser"]:
            token["role"] = 1
        else:
            token["role"] = group['id']
        # ...

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        sso = request.data.get("sso")

        response = super().post(request, *args, **kwargs)

        if sso:
            return response
        else:
            json_data = ConvertQuerysetToJson(
                User.objects.filter(username=username))
            staff = json_data.get("is_staff")
            if staff == True:
                return response
            else:
                raise PermissionDenied(
                    "User is not staff and cannot generate a token.")


# Change Password view


@permission_classes([IsAuthenticated])
class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    # permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer


# Get employee registration details
@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def getEmpRegDetails(request):
    user = request.user
    employee = User.objects.all()
    serializer = RegisterSerializer(employee, many=True)
    return Response(serializer.data)


# Update user active


class UpdateActiveView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = UpdateActiveSerializer


# Create super user


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_users(request):
    # print("user save data", request.data)

    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    # is_staff = True

    if User.objects.filter(username=username):
        # print("if", User.objects.filter(username=username))
        return Response("User already exist", status=status.HTTP_400_BAD_REQUEST)
    users = User.objects.create_user(username, email, password, is_staff=1)
    temp = User.objects.filter(username=users)
    # print(temp)
    return Response("User Added successfully", status=status.HTTP_200_OK)


# Create super user
@api_view(["POST"])
def ms_save_users(request):
    # print("user data", request.data)

    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if User.objects.filter(username=username):
        # print("if", User.objects.filter(username=username))
        return Response("User already exist", status=status.HTTP_400_BAD_REQUEST)
    users = User.objects.create_user(username, email, password)
    temp = User.objects.filter(username=users)
    # print(temp)
    return Response("User Added successfully", status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def user_registration(request):
    # print(request)
    is_staff = request.data.get("country")
    data = {
        "username": request.data.get("username"),
        "email": request.data.get("email"),
        "password": request.data.get("password"),
        "password2": request.data.get("cpassword"),
        "is_staff": request.data.get("country"),
        # 'no_of_org_funcational_levels': request.data.get('no_of_org_funcational_levels'),
        # 'created_by': request.data.get('created_by'),
        # 'last_updated_by': request.data.get('last_updated_by')
    }
    serializer = RegisterSerializer(data=data)
    if serializer.is_valid():
        # serializer.save()
        # print(data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    # print(serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # return Response(data)


# Get Auth Group


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_auth_group(request):
    auth_group = Group.objects.all()
    serializer = auth_group_serializer(auth_group, many=True)
    return Response(serializer.data)


def ConvertQuerysetToJson(qs):
    if qs == None:
        return "Please provide valid Django QuerySet"
    else:
        json_data = {}
        for i in qs:
            i = i.__dict__
            i.pop("_state")
            json_data.update(i)
    return json_data


# Get User Group details range
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_range_user_groups(request, start, end):
    try:
        group_user_dict = {
            group.id: group.user_set.values_list(
                "id", "username", "email", "is_active", flat=False
            )
            for group in Group.objects.all()
        }
        act_json = []
        for i in group_user_dict:
            temp = ConvertQuerysetToJson(Group.objects.filter(id=i))

            for j in group_user_dict[i]:
                # print("i", j)

                temp_json = {
                    "user_id": j[0],
                    "user_name": j[1],
                    "user_mail": j[2],
                    "is_active": j[3],
                    "user_group_id": i,
                    "user_group_name": temp["name"],
                }
                act_json.append(temp_json)
        # print("act_json", act_json[start:end], len(act_json))

    except Exception as e:
        print("Exception", e)

    return Response({"data": act_json[start:end], "data_length": len(act_json)})


# Get USer Group details
@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def get_user_groups(request, id=0):
    # def get_range_perspectives(request, start, end):
    # pers_len = perspectives.objects.filter(delete_flag='N').count()
    # pers = perspectives.objects.filter(delete_flag='N')[start:end]
    # serializer = perspectives_serializer(pers, many=True)
    # return Response({"data": serializer.data, "data_length": pers_len})
    try:
        superadmin = request.data.get('is_superuser')
        if id == 0:
            group_user_dict = {
                group.id: group.user_set.values_list(
                    "id", "username", "email", "is_active", "is_staff", flat=False
                )
                for group in Group.objects.all()
            }
        else:
            group_user_dict = {
                group.id: User.objects.filter(id=id).values_list(
                    "id", "username", "email", "is_active", "is_staff", flat=False
                ) if superadmin else group.user_set.filter(id=id).values_list(
                    "id", "username", "email", "is_active", "is_staff", flat=False
                )
                for group in Group.objects.all()
            }
            # group_user_dict = {
            #     group.id: group.user_set.values_list(
            #         "id", "username", "email", "is_active", "is_staff", flat=False
            #     ).filter(id=id)
            #     for group in Group.objects.all()
            # }
        act_json = []
        for i in group_user_dict:
            temp = ConvertQuerysetToJson(Group.objects.filter(id=i))
            for j in group_user_dict[i]:
                temp_json = {
                    "user_id": j[0],
                    "user_name": j[1],
                    "user_mail": j[2],
                    "is_active": j[3],
                    "is_staff": j[4],
                    "user_group_id": i,
                    "user_group_name": temp["name"],
                }
                act_json.append(temp_json)

    except Exception as e:
        print("Exception", e)

    return Response(act_json)


# Get User Group details range
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_range_user_groups(request, start, end):
    # def get_range_perspectives(request, start, end):
    # pers_len = perspectives.objects.filter(delete_flag='N').count()
    # pers = perspectives.objects.filter(delete_flag='N')[start:end]
    # serializer = perspectives_serializer(pers, many=True)
    # return Response({"data": serializer.data, "data_length": pers_len})
    try:
        group_user_dict = {
            group.id: group.user_set.values_list(
                "id", "username", "email", "is_active", flat=False
            )
            for group in Group.objects.all()
        }
        act_json = []
        for i in group_user_dict:
            temp = ConvertQuerysetToJson(Group.objects.filter(id=i))

            for j in group_user_dict[i]:
                # print("i", j)

                temp_json = {
                    "user_id": j[0],
                    "user_name": j[1],
                    "user_mail": j[2],
                    "is_active": j[3],
                    "user_group_id": i,
                    "user_group_name": temp["name"],
                }
                act_json.append(temp_json)
        # print("act_json", act_json[start:end], len(act_json))

    except Exception as e:
        print("Exception", e)

    return Response({"data": act_json[start:end], "data_length": len(act_json)})


# Create user groups add
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ins_user_groups(request):
    user_id = request.data.get("user_id")
    group_id = request.data.get("group_id")

    user = User.objects.get(id=user_id)
    group = Group.objects.get(id=group_id)
    user.groups.add(group)

    return Response("User Added successfully", status=status.HTTP_200_OK)


# Create user groups add
@api_view(["POST"])
def ms_ins_user_groups(request):
    user_id = request.data.get("user_id")
    group_id = request.data.get("group_id")

    user = User.objects.get(id=user_id)
    group = Group.objects.get(id=group_id)

    user.groups.add(group)

    return Response("User Added successfully", status=status.HTTP_200_OK)


# Create user groups Update


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upd_user_groups(request):
    user_id = request.data.get("id")
    user_name = request.data.get("username")
    user_mail = request.data.get("email")
    group_id = request.data.get("group")
    is_active = request.data.get("is_active")
    is_active = True if is_active == "true" or "Yes" else False

    user = User.objects.get(id=user_id)
    group = Group.objects.get(id=group_id)
    if User.objects.filter(username=user_name).exclude(id=user_id):
        # print("if", User.objects.filter(username=user_name))
        return Response("User already exist", status=status.HTTP_400_BAD_REQUEST)
    user.groups.set([group])
    user.email = user_mail
    user.username = user_name
    user.is_active = is_active
    print(user, User.objects.filter(username=user_name).exclude(id=user_id))
    user.save()

    return Response("User Updated successfully", status=status.HTTP_200_OK)


# demo Ins user group details


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ins_group_access(request):
    listData = request.data
    if not listData:
        return Response(
            {"group_id": "This field is may not be empty"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        if 'group_name' in dict(listData[list(listData)[0]]):
            data = {
                'name': dict(listData[list(listData)[0]])['group_name']
            }
            group_serializer = auth_group_serializer(data=data)
            if group_serializer.is_valid():
                group_serializer.save()
                for x in listData:
                    if x != '0':
                        data = {
                            "menu_id": listData[x]["menu_id"],
                            "group_id": group_serializer.data['id'],
                            "add": listData[x]["add"] if 'add' in listData[x] else 'N',
                            "edit": listData[x]["edit"] if 'edit' in listData[x] else 'N',
                            "view": listData[x]["view"] if 'view' in listData[x] else 'N',
                            "delete": listData[x]["delete"] if 'delete' in listData[x] else 'N',
                            "created_by": listData[x]["created_by"],
                            "last_updated_by": listData[x]["last_updated_by"],
                        }
                        serializer = group_access_definition_serializer(
                            data=data)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(group_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# View all
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_navigation_menu_details(request, id=0):
    if id == 0:
        org = navigation_menu_details.objects.filter(delete_flag="N")
    else:
        org = navigation_menu_details.objects.filter(menu_id=id)

    serializer = navigation_menu_details_serializer(org, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_single_navigation_menu_details(request, id):
    try:
        data = navigation_menu_details.objects.filter(page_number=id)
        if not data:
            return Response({"message": "Navigation menu not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = navigation_menu_details_serializer(data, many=True)
            return Response(serializer.data)
    except Exception as e:
        return Response({"message": f"Something went wrong: {str(e)}"},  status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Insert navigation_menu_details


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ins_navigation_menu_details(request):
    listData = request.data
    # print("listData", listData, "length", len(listData))
    all_items = navigation_menu_details.objects.all()
    for x in range(len(listData)):
        data = {
            "menu_name": listData[x]["menu_name"],
            "parent_menu_id": listData[x]["parent_menu_id"],
            "url": listData[x]["url"],
            "created_by": listData[x]["created_by"],
            "last_updated_by": listData[x]["last_updated_by"],
        }
        check_item = all_items.filter(menu_name=listData[x]["menu_name"])
        serializer = navigation_menu_details_serializer(data=data)
        if serializer.is_valid() and not check_item:
            try:
                serializer.save()
            except IntegrityError:
                print(IntegrityError)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ins group access definition
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ins_group_access_definition(self, request, id, format=None):
    listData = request.data
    if not listData:
        return Response(
            {"group_id": "This field is may not be empty"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        for x in listData:
            data = {
                "menu_id": listData[x]["menu_id"],
                "group_id": listData[x]["group_id"],
                "add": listData[x]["add"],
                # 'add': {{request.data.get('add')| default_if_none:'Y'}},
                "edit": listData[x]["edit"],
                "view": listData[x]["view"],
                "delete": listData[x]["delete"],
                "created_by": listData[x]["created_by"],
                "last_updated_by": listData[x]["last_updated_by"],
            }
            serializer = group_access_definition_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)


# upd group access definition


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upd_group_access_definition(request, id):
    listData = request.data
    print(type(listData))
    if not listData:
        return Response(
            {"user_id": "This field is may not be empty"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        all_item = group_access_definition.objects.all()
        for x in listData:
            data = {
                "menu_id": listData[x]["menu_id"],
                "group_id": listData[x]["group_id"],
                "add": listData[x]["add"],
                # 'add': {{request.data.get('add')| default_if_none:'Y'}},
                "edit": listData[x]["edit"],
                "view": listData[x]["view"],
                "delete": listData[x]["delete"],
                "created_by": listData[x]["created_by"],
                "last_updated_by": listData[x]["last_updated_by"],
            }

            selected_item = all_item.filter(
                menu_id=listData[x]["menu_id"], group_id=id
            ).first()
            if not selected_item:
                serializer = group_access_definition_serializer(data=data)
                if serializer.is_valid():
                    serializer.save()
            else:
                serializer = group_access_definition_serializer(
                    instance=selected_item, data=data
                )
                if serializer.is_valid():
                    serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


# User


# View all
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    org = User.objects.filter(is_active="1")
    serializer = user_serializer(org, many=True)
    return Response(serializer.data)


# Join group and group_access_definition table view


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def group_group_access(request, id=0, menu_id=0):
    if id == 0:
        org = navigation_menu_details.objects.filter(delete_flag="N")
        serializer = navigation_menu_details_serializer(org, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        if menu_id == 0:
            reports = group_access_definition.objects.select_related(
                "group_id").filter(group_id=id)
        else:
            superadmin = User.objects.filter(id=id).values('is_superuser')
            grp_id = ConvertQuerysetToJson(
                User.objects.get(id=id).groups.all())
            if superadmin[0]['is_superuser']:
                reports = group_access_definition.objects.select_related(
                    "group_id", "menu_id"
                ).filter(group_id=1, menu_id=menu_id)
            else:
                reports = group_access_definition.objects.select_related(
                    "group_id", "menu_id"
                ).filter(group_id=grp_id["id"], menu_id=menu_id)
            # reports = group_access_definition.objects.select_related("group_id").filter(group_id=id, menu_id=menu_id)
        data = group_group_access_serializer(
            reports, many=True, context={"request": request}
        ).data
        return Response(data, status=status.HTTP_200_OK)


# get group access definition


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_group_access_definition(request, id=0):
    if id == 0:
        org = group_access_definition.objects.filter(delete_flag="N")
    else:
        org = group_access_definition.objects.filter(group_id=id)

    serializer = group_access_definition_serializer(org, many=True)
    return Response(serializer.data)


# ----settings---- #
# Get


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_settings(request, id=0):
    if id == 0:
        pers = settings.objects.filter(delete_flag="N")
    else:
        pers = settings.objects.filter(user_id=id)
    serializer = settings_serializer(pers, many=True)
    return Response(serializer.data)


# Put and insert
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upd_settings(request, id):
    listData = request.data
    if not listData:
        return Response(
            {"user_id": "This field is may not be empty"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    else:
        all_item = settings.objects.all()
        for x in listData:
            data = {
                "variable_name": listData[x]["variable_name"],
                "value": listData[x]["value"],
                "user_id": id,
                "created_by": listData[x]["created_by"],
                "last_updated_by": listData[x]["last_updated_by"],
            }

            selected_item = all_item.filter(
                variable_name=listData[x]["variable_name"], user_id=id
            ).first()
            if not selected_item:
                serializer = settings_serializer(data=data)
                if serializer.is_valid():
                    serializer.save()
            else:
                serializer = settings_serializer(
                    instance=selected_item, data=data)
                if serializer.is_valid():
                    serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


# todo csv uplode for user and user_group working code
def using_pandas(file_path, table, id):
    # print("table_name",table)
    # uri = "mysql://root:@localhost:3306/score_card"
    df = pd.read_csv(file_path)
    df = df.rename(columns=lambda x: x.lower().replace(" ", "_"))

    if table == "user":
        new_cols = pd.DataFrame(
            {
                "date_joined": [date.today()],
                "is_active": [1],
                "is_staff": [1],
                "is_superuser": [0],
            }
        )
        df = pd.concat([df, new_cols], axis=1)

    # ? code for geting uri dynamically
    db_settings = def_set.DATABASES["default"]
    uri = f"{db_settings['ENGINE'].split('.')[-1]}://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
    # ? code for geting uri dynamically end

    engine = create_engine(uri)
    
    if table == "user_groups":
        # print("if")
        df_list_group = []
        df_list_user = []
        for i in df.user_group:
            group_data = ConvertQuerysetToJson(Group.objects.filter(name=i))
            df_list_group.append(group_data["id"])
        for i in df.username:
            user_data = ConvertQuerysetToJson(User.objects.filter(username=i))
            df_list_user.append(user_data["id"])
        df_data = {"group_id": df_list_group, "user_id": df_list_user}
        new_df = pd.DataFrame(df_data)
        new_df.to_sql("auth_" + table, con=engine,
                      if_exists="append", index=False)
        # print("new_df", new_df)
    elif table == "user":
        # print("elif")
        df.to_sql("auth_" + table, con=engine, if_exists="append", index=False)
    else:
        # print("else")
        df.to_sql("tb_sc_" + table, con=engine,
                  if_exists="append", index=False)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Csv_insert(request, id):
    if "file" in request.FILES:
        file = request.FILES["file"]
        table = request.data.get("table")
        try:
            using_pandas(file, table, id)
        except Exception as e:
            error_message = str(e)
            start_index = error_message.find("Duplicate entry")
            end_index = error_message.find('"', start_index)
            duplicate_entry_message = error_message[start_index: end_index + 1]

            # Print the extracted error message
            # print("Error", error_message)
            return Response(
                {"error": duplicate_entry_message.replace('"', "")},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            return Response("Success", status=status.HTTP_200_OK)


# todo user and user_group code ends


# forgot_password


@api_view(["POST"])
def forgot_password(request):
    email = request.data
    check_email = ConvertQuerysetToJson(
        User.objects.filter(email=email, is_active=1))
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    numbers = string.digits
    special_characters = string.punctuation

    if check_email:
        combinedPassword = (
            random.choice(uppercase_letters)
            + random.choice(lowercase_letters)
            + random.choice(numbers)
            + random.choice(special_characters)
        )

        randomPassword = "".join(
            random.choice(lowercase_letters) + random.choice(uppercase_letters)
            for _ in range(len(combinedPassword) + 1)
        )

        # finalPassword = "".join(randomPassword + random.choice(special_characters))

        subject = "Password reset"
        body = (
            """
            <html>
            <body>
            <div style="text-align:center;">
            <p>Hi """
            + check_email["username"].capitalize()
            + """,</p>
            <p>Congratulations. You have successfully reset your password.</p>
            <p>Please use the below password to login</p><br>
            <b style="display: inline; padding: 10px;font-size: 18px;background: cornflowerblue;">"""
            + str(randomPassword)
            + """</b><br><br>
            </div>
            <i>Thanks, <br> Cittabase</i>
            </body>
            </html>
            """
        )
        u = User.objects.get(id=check_email["id"])
        u.set_password(randomPassword)
        u.save()
        mail_res = smtp_mail.send_mail(
            to=email, subject=subject, body=body, type="html"
        )
        return Response(status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


# ***User Profile***


# View all
@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_user_profile(request, id=0):
    if id == 0:
        user = user_profile.objects.filter(delete_flag="N")
    else:
        user = user_profile.objects.filter(user_id=id)

    serializer = user_profile_serializer(user, many=True)

    return Response(serializer.data)


# Add
@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def ins_user_profile(request):
    data = {
        "user_id": request.data.get("user_id"),
        "username": request.data.get("username"),
        "profile_pic": request.data.get("profile_pic"),
        "first_name": request.data.get("first_name"),
        "last_name": request.data.get("last_name"),
        "email": request.data.get("email"),
        "temporary_address": request.data.get("temporary_address"),
        "permanent_address": request.data.get("permanent_address"),
        "contact": request.data.get("contact"),
        "user_group": request.data.get("user_group"),
        "user_status": request.data.get("user_status"),
        "created_by": request.data.get("created_by"),
        "last_updated_by": request.data.get("last_updated_by"),
    }
    if 'profile_pic' not in request.data:
        data["profile_pic"] = None
    serializer = user_profile_serializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User Profile update

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upd_user_profile(request, id):
    item = user_profile.objects.get(id=id)
    data = request.data

    if item.profile_pic:
        if len(item.profile_pic) > 0 and item.profile_pic != data["profile_pic"]:
            # print("path", org_settings_view.logo.path)
            os.remove(item.profile_pic.path)

    if item.username != data["username"]:
        item.username = data["username"]
    if item.profile_pic != data["profile_pic"]:
        item.profile_pic = data["profile_pic"]
    if item.first_name != data["first_name"]:
        item.first_name = data["first_name"]
    if item.last_name != data["last_name"]:
        item.last_name = data["last_name"]
    if item.email != data["email"]:
        item.email = data["email"]
    if item.temporary_address != data["temporary_address"]:
        item.temporary_address = data["temporary_address"]
    if item.permanent_address != data["permanent_address"]:
        item.permanent_address = data["permanent_address"]
    if item.contact != data["contact"]:
        item.contact = data["contact"]
    if item.user_group != data["user_group"]:
        item.user_group = data["user_group"]
    if item.user_status == True:
        item.user_status = True
    else:
        item.user_status = False
    if item.created_by != data["created_by"]:
        item.created_by = data["created_by"]
    if item.last_updated_by != data["last_updated_by"]:
        item.last_updated_by = data["last_updated_by"]

    item.save()
    serializer = user_profile_serializer(item)
    return Response(serializer.data)


# Delete


@api_view(["PUT"])
# @permission_classes([IsAuthenticated])
def del_user_profile(request, id):
    Userdata = user_profile.objects.get(id=id)
    data = request.data
    if Userdata.delete_flag != data["delete_flag"]:
        Userdata.delete_flag = data["delete_flag"]
    if Userdata.last_updated_by != data["last_updated_by"]:
        Userdata.last_updated_by = data["last_updated_by"]
    Userdata.save()
    serializer = user_profile_serializer(Userdata)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def updatesession(request, uid=0, update=""):
    item = request.data
    now = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    expiredOneday = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S") + timedelta(hours=24)
    count_session = session.objects.filter(uid=uid, status=1)
    if update == "update":
        data = {
            "uid": uid,
            "sid": item["access"],
            "expired": expiredOneday.strftime("%Y-%m-%d %H:%M:%S"),
            "status": 1,
        }
        exist_session = session.objects.get(uid=uid, sid=item["prev_token"])
        # exist_session = session.objects.filter(uid=uid).update(lasttime=item['last_time'])
        serializer = session_serializer(instance=exist_session, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    elif update == "close":
        cdata = {
            "lasttime": item["last_time"],
            "status": 0,
        }
        # exist_session = session.objects.filter(uid=uid, sid=item['access'])
        exist_session = session.objects.filter(uid=uid, sid=item["access"]).update(
            lasttime=item["last_time"], status=0
        )
        # serializer = session_serializer(instance=exist_session, data=cdata)
        if exist_session:
            # serializer.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    elif update == "shotdown":
        exist_session = session.objects.filter(uid=uid, sid=item["access"]).update(
            lasttime=item["last_time"]
        )
        if exist_session:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        if len(count_session) < 10:
            data = {
                "uid": uid,
                "sid": item["access"],
                "logintime": item["login_time"],
                "expired": expiredOneday.strftime("%Y-%m-%d %H:%M:%S"),
                "status": 1,
            }
            serializer = session_serializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def deletesession(request, uid=0):
    # exist_session = session.objects.filter(uid=uid).delete()
    exist_session = session.objects.filter(uid=uid).update(sta=item["last_time"])
    if exist_session:
        return Response(status=status.HTTP_201_CREATED)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


def session_active_check():
    active_session = session.objects.filter(status=1).values()
    for i in active_session:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if i["expired"] < current_date:
            exist_session = session.objects.filter(uid=i["uid"], sid=i["sid"]).update(
                status=0
            )
    return Response(status=status.HTTP_200_OK)

# Session Configuration

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_session_configuration(request):
    sessionData = session_configuration.objects.filter(delete_flag='N')
    serializer = session_configuration_serializer(sessionData, many=True)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ins_upd_session_configuration(request, id):
    if id == 0:
        data = {
        "idle_time": request.data.get("idle_time"),
        "session_time": request.data.get("session_time"),
        "created_by": request.data.get("created_by"),
        "last_updated_by": request.data.get("last_updated_by"),
        }
        serializer = session_configuration_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        data = {
            "idle_time": request.data.get("idle_time"),
            "session_time": request.data.get("session_time"),
            "last_updated_by": request.data.get("last_updated_by"),
        }
        exist_session = session_configuration.objects.get(id=id, delete_flag="N")
        serializer = session_configuration_serializer(instance=exist_session, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# SSO Insert
@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def ins_sso(request):
    data = {
        "app_id": request.data.get("app_id"),
        "tenant_id": request.data.get("tenant_id"),
        "created_by": request.data.get("created_by"),
        "last_updated_by": request.data.get("last_updated_by"),
    }

    serializer = sso_configure_serializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# SSO Get
@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_sso(request, id=0):
    if id == 0:
        sso = sso_configure.objects.filter(delete_flag="N")
    else:
        sso = sso_configure.objects.filter(id=id)
    serializer = sso_configure_serializer(sso, many=True)
    return Response(serializer.data)


# SSO Update
@api_view(["PUT"])
# @permission_classes([IsAuthenticated])
def upd_sso(request, id):
    item = sso_configure.objects.get(id=id)
    print(request.data)
    serializer = sso_configure_serializer(instance=item, data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def ins_upd_license(request, id):
    item = user_license.objects.filter(user_id=id)
    data = {
        "license_key": request.data.get("key"),
        "user_id": id,
        "created_by": id,
        "last_updated_by": id,
    }
    if len(item) == 0:
        serializer = user_license_serializer(data=data)
    else:
        exist = user_license.objects.get(user_id=id)
        serializer = user_license_serializer(instance=exist, data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        print("Error", serializer.errors)


@api_view(["GET"])
def get_license(request):
    current_datetime = datetime.datetime.now().date()
    # print("current_datetime", current_datetime)
    licensed = user_license.objects.filter(delete_flag="N")
    serializer = user_license_serializer(licensed, many=True)
    return Response(
        {"data": serializer.data, "current_date": current_datetime},
        status=status.HTTP_200_OK,
    )


# Global helper api's

# GET


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_helper(request, id=0):
    if id == 0:
        chart_options = helper.objects.all()
    else:
        chart_options = helper.objects.filter(page_no=id)

    serializer = helper_serializer(chart_options, many=True)
    return Response(serializer.data)


# GET


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_warnings(request, id=0):
    if id == 0:
        get_warning_data = warnings.objects.all()
    else:
        get_warning_data = warnings.objects.filter(id=id)

    serializer = warnings_serializer(get_warning_data, many=True)
    return Response(serializer.data)

    
# *** Query Builder Connection definition***


# View all

@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_rb_connect_definition_table(request, id=0):
    if id == 0:
        rb = rb_connect_definition_table.objects.filter(delete_flag="N")
    else:
        rb = rb_connect_definition_table.objects.filter(id=id)

    serializer = rb_connect_definition_table_serializer(rb, many=True)
    return Response(serializer.data)

import json 
@api_view(["POST"])
def get_rb_table(request, id=0):
    all_data={}
    definition_data = request.data
    connection_obj = rb_connect_definition_table.objects.filter(delete_flag="N", id=definition_data['connection_id'])
    connection_serializer = rb_connect_definition_table_serializer(connection_obj, many=True)
    if len(connection_serializer.data) > 0:
        all_data['Page1'] = definition_data
        all_data['Page1']['savedConnectionItems'] = json.loads(json.dumps(connection_serializer.data))[0] if len(connection_serializer.data) == 1 else json.loads(json.dumps(connection_serializer.data))
        if definition_data['query_type'] == False:
            table_obj = query_builder_table.objects.filter(delete_flag="N", query_id=definition_data['id']).values('id','table_name','table_id')
            all_data['Page2'] = table_obj
            # all_data['Page2'] = table_obj[0] if len(table_obj) == 1 else table_obj
            all_data['Page3'] = []
            all_data['Page4'] = {}
            all_data['Page5'] = []
            all_data['Page6'] = {}
            all_data['Page7'] = []
            temp_alias = []
            temp_column_page4 = []
            temp_aggregate = []
            for table_data in table_obj:
                temp_columns_page4 = []
                column_obj = query_builder_table_columns.objects.filter(delete_flag="N", table_column_query_id=definition_data['id'], table_column_table_id=table_data['id']).values()
                for column_data in column_obj:
                    aggregation_obj = query_builder_aggeration_function_table.objects.filter(delete_flag="N", table_aggragate_query_id=definition_data['id'], table_aggregate_table_id=table_data['id'], table_aggregate_column_id=column_data['id']).values()
                    temp_column = {}
                    temp_column['table_name'] = table_data['table_name']
                    temp_column['column'] = {
                        'id': column_data['id'],
                        'columnName': column_data['column_name'],
                        'dataType': column_data['column_data_type'],
                        'tableId': table_data['table_id'],
                    }
                    temp_columns_page4.append({
                        'id': column_data['id'],
                        'columnName': column_data['column_name'],
                        'dataType': column_data['column_data_type'],
                        'tableId': table_data['table_id']
                    })
                    if column_data['alias_name'] != None:
                        temp_alias.append({
                            'id': column_data['id'],
                            "selectedTableName": table_data['table_name'],
                            "selectedColumnName": column_data['column_name'],
                            "setAliasName": column_data['alias_name']
                        })
                    all_data['Page3'].append(temp_column) 
                    if len(aggregation_obj) > 0:
                        all_data['Page5'].append({
                            "id": aggregation_obj[0]['id'] if len(aggregation_obj) == 1 else '',
                            "selectedTable": table_data['table_name'],
                            "selectedColumn": column_data['column_name'],
                            "selectedAttribute": aggregation_obj[0]['agg_fun_name'] if len(aggregation_obj) == 1 else ''
                        }) 
                temp_column_page4.append({
                    "table_name": table_data['table_name'],
                    "table_columns": temp_columns_page4
                })
                where_obj = query_builder_table_column_filter.objects.filter(delete_flag="N", tab_filter_query_id=definition_data['id'], tab_filter_tale_id=table_data['id']).values()
                for where_data in where_obj:
                    all_data['Page7'].append({
                        "id": where_data['id'],
                        "table_name": table_data['table_name'],
                        "column_name": where_data['column_name'],
                        "operator": where_data['column_filter'],
                        "value": where_data['column_value']
                    })
            all_data['Page4']['getcolumnalias'] = temp_alias
            all_data['Page4']['getSelectedColumn'] = temp_column_page4
            all_data['Page6']['getjoinrows'] = []
            all_data['Page6']['getallcolumns'] = []
            join_obj = query_builder_table_joins.objects.filter(delete_flag="N", tab_join_query_id=definition_data['id']).values()
            for join_data in join_obj:
                selected_table_1 = query_builder_table.objects.filter(delete_flag="N", id=join_data['tab_join_table_id_one_id']).values('table_name')
                selected_table_2 = query_builder_table.objects.filter(delete_flag="N", id=join_data['tab_join_table_id_two_id']).values('table_name')
                all_data['Page6']['getjoinrows'].append({
                    "id": join_data['id'],
                    "selectedTable": selected_table_1[0]['table_name'] if len(selected_table_1) == 1 else '',
                    "selectedColumn": join_data['join_column_name1'],
                    "selectedAttribute": join_data['join_type'],
                    "selectedTable2": selected_table_2[0]['table_name'] if len(selected_table_2) == 1 else '',
                    "selectedColumn2": join_data['join_column_name2']
                })
    return Response(all_data, status=status.HTTP_200_OK)


# GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_range_rb_connect_definition_table(request, start, end):
    pers_len = rb_connect_definition_table.objects.filter(delete_flag="N").count()
    pers = rb_connect_definition_table.objects.filter(delete_flag="N")[start:end]
    pers_csv_export = rb_connect_definition_table.objects.filter(delete_flag="N")
    serializer = rb_connect_definition_table_serializer(pers, many=True)
    serializer_csv_export = rb_connect_definition_table_serializer(
        pers_csv_export, many=True)
    return Response(
        {
            "data": serializer.data,
            "data_length": pers_len,
            "csv_data": serializer_csv_export.data,
        }
    )


# ADD
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ins_rb_connect_definition_table(request):
    data = {
        "connection_name": request.data.get("connection_name"),
        "database_name": request.data.get("database_name"),
        "connection_type": request.data.get("connection_type"),
        "user_name": request.data.get("user_name"),
        "password": request.data.get("password"),
        "host_id": request.data.get("host_id"),
        "port": request.data.get("port"),
        "service_name_or_SID": request.data.get("service_name_or_SID"),
        "schema_name": request.data.get("schema_name"),
        "account_id": request.data.get("account_id"),
        "warehouse_id": request.data.get("warehouse_id"),
        "role": request.data.get("role"),

        "auth_type": request.data.get("auth_type"),
        "auth_url": request.data.get("auth_url"),
        "body": request.data.get("body"),
        "user_id": request.data.get("user_id"),
        "data_enpoint_url": request.data.get("data_enpoint_url"),
        "method": request.data.get("method"),
        "created_by": request.data.get("created_by"),
        "last_updated_by": request.data.get("last_updated_by"),
    }
    print(f"==>> data: {data}")

    serializer = rb_connect_definition_table_serializer(data=data)

    all_serializer_fields = list(serializer.fields.keys())

    print("all_serializer_fields", all_serializer_fields)

    # Fields to exclude
    fields_to_exclude = ['id', 'created_by', 'last_updated_by', 'created_date']

    # Remove the excluded fields from the list of field names
    required_serializer_fields = [
        field for field in all_serializer_fields if field not in fields_to_exclude]

    # print("required_serializer_fields",required_serializer_fields)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        error_data = serializer.errors
        # print("error_data", error_data, len(error_data))
        e_code = []
        e_msg = []
        e_field = []
        # Iterate over each field's errors
        for field, error_list in error_data.items():
            for error_data in error_list:
                # Access the error code
                error_code = error_data.code
                e_code.append(error_code)
                e_msg.append(error_data)
                e_field.append(field)

        # print("e_code", e_code, "length", len(e_code))
        # print("e_msg", e_msg, "length", len(e_msg))
        # print("e_field", e_field, "length", len(e_field))

        # Remove the excluded fields from the list of field names
        non_e_field = [
            for_field for for_field in required_serializer_fields if for_field not in e_field]

        # print("non_e_field",non_e_field)

        data_warning = warnings.objects.filter(
            error_code__in=e_code, error_from="Server"
        )
        serializer_warning = warnings_serializer(data_warning, many=True)
        # print("serializer_warning length", serializer_warning.data)

        # ! test validation on Backend level

        field_arr = []
        for iter in range(len(e_code)):
            for j in serializer_warning.data:
                # print("out : ", e_code[iter], j["error_code"])
                if e_code[iter] == j["error_code"]:
                    field_arr.append(
                        (j["error_msg"]).replace(
                            "%1", e_field[iter].replace("_", " "))
                    )
                    # print("true")
                    # print("j:", j["error_msg"])
                else:
                    print("false")
                    print("i:", e_code[iter])

        # print("field_arr", field_arr)

        data = []
        for i in range(len(e_code)):
            # print(f"Error code for field '{field}': {error_code}")
            data.append({e_field[i]: [field_arr[i]]})
        # print("data", data)

        for i in range(len(non_e_field)):
            data.append({non_e_field[i]: ''})
        # print("data", data)

        def order_data(data):
            # Define the desired field order
            field_order = {
                "connection_name": 0,
                "user_name": 1,
                "password": 2,
                "account_id": 3,
                "host_id": 3,
                "port": 4,
                "schema_name": 4,
                "database_name": 5,
                "service_name_or_SID": 5,
                "warehouse_id": 6,
                "role": 7,
                "connection_type": 8,
                "auth_type": 9,
                "body" : 10,
                "auth_url": 11,
                "user_id": 12,
                "data_enpoint_url": 13,
                "method": 14,
            }

            # Sort the data based on the field order
            sorted_data = sorted(data, key=lambda item: field_order.get(
                list(item.keys())[0], float('inf')))

            return sorted_data

        # Order the data
        ordered_data = order_data(data)

        # Print the ordered data
        # print("ordered_data",ordered_data)

        return Response(ordered_data, status=status.HTTP_404_NOT_FOUND)


# ADD
@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def rb_test_db_connection(request):
    data = {
        "connection_name": request.data.get("connection_name"),
        "database_name": request.data.get("database_name"),
        "connection_type": request.data.get("connection_type"),
        "user_name": request.data.get("user_name"),
        "password": request.data.get("password"),
        "host_id": request.data.get("host_id"),
        "port": request.data.get("port"),
        "service_name_or_SID": request.data.get("service_name_or_SID"),
        "schema_name": request.data.get("schema_name"),
        "account_id": request.data.get("account_id"),
        "warehouse_id": request.data.get("warehouse_id"),
        "role": request.data.get("role"),
        "created_by": request.data.get("created_by"),
        "last_updated_by": request.data.get("last_updated_by"),
    }

    serializer = rb_connect_definition_table_serializer(data=data)
    print(f"==>> data: {data}")

    all_serializer_fields = list(serializer.fields.keys())

    
    # Fields to exclude
    fields_to_exclude = ['id', 'created_by', 'last_updated_by', 'created_date']

    # Remove the excluded fields from the list of field names
    required_serializer_fields = [
        field for field in all_serializer_fields if field not in fields_to_exclude]

    if serializer.is_valid():
        print("VALID")
        try:
            db_type = serializer.data['connection_type']
            print(f"==>> db_type: {db_type}")
            
            if db_type == 'MYSQL':
                try:
                    mydb = sqlConnect.connect(
                        host=serializer.data['host_id'],
                        user=serializer.data['user_name'],
                        password=serializer.data['password'],
                        database=serializer.data['database_name'],
                        port=serializer.data['port']
                    )
                    
                    # Check if the connection is successful
                    if mydb.is_connected():
                        mydb.close()
                        return Response('Connected', status=status.HTTP_200_OK)
                    else:
                        return Response("Failed", status=status.HTTP_400_BAD_REQUEST)
                    
                except sqlConnect.Error as e:
                    # Handle the database-related errors, including syntax errors
                    error_message = f"MYSQL error : {str(e)}"

                    return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

            elif db_type == "Oracle":
                try:
                    connection_str = f"{serializer.data['user_name']}/{serializer.data['password']}@{serializer.data['host_id']}:{serializer.data['port']}/{serializer.data['service_name_or_SID']}"
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
                        'user': serializer.data['user_name'],
                        'password': serializer.data['password'],
                        'account': serializer.data['account_id'],
                        'warehouse': serializer.data['warehouse_id'],
                        'database': serializer.data['database_name'],
                        'schema': serializer.data['schema_name'],
                        'role': serializer.data['role'],
                    }

                    if snowflake.connector.connect(**connection_str):
                        connection = snowflake.connector.connect(**connection_str)
                        connection.close()
                        return Response('Connected', status=status.HTTP_200_OK)
                    else:
                        return Response('Failure', status=status.HTTP_400_BAD_REQUEST)
                
                except snowflake.connector.errors.DatabaseError as e:
                    # Handle Oracle errors
                    error_message = f"Snowflake error: {str(e)}"
                    return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                return Response('Database not found!', status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            # Handle any database connection errors
            return Response(f'Database connection error: {str(e)}', status=status.HTTP_400_BAD_REQUEST)
        
        # serializer.save()
        # return Response('serializer.data', status=status.HTTP_200_OK)
    else:
        print("INVALID")
        error_data = serializer.errors
        print("error_data", error_data, len(error_data))
        e_code = []
        e_msg = []
        e_field = []
        # Iterate over each field's errors
        for field, error_list in error_data.items():
            for error_data in error_list:
                # Access the error code
                error_code = error_data.code
                e_code.append(error_code)
                e_msg.append(error_data)
                e_field.append(field)

        # print("e_code", e_code, "length", len(e_code))
        # print("e_msg", e_msg, "length", len(e_msg))
        # print("e_field", e_field, "length", len(e_field))

        # Remove the excluded fields from the list of field names
        non_e_field = [
            for_field for for_field in required_serializer_fields if for_field not in e_field]

        # print("non_e_field",non_e_field)

        data_warning = warnings.objects.filter(
            error_code__in=e_code, error_from="Server"
        )
        serializer_warning = warnings_serializer(data_warning, many=True)
        # print("serializer_warning length", serializer_warning.data)

        # ! test validation on Backend level

        field_arr = []
        for iter in range(len(e_code)):
            for j in serializer_warning.data:
                # print("out : ", e_code[iter], j["error_code"])
                if e_code[iter] == j["error_code"]:
                    field_arr.append(
                        (j["error_msg"]).replace(
                            "%1", e_field[iter].replace("_", " "))
                    )
                    # print("true")
                    # print("j:", j["error_msg"])
                else:
                    print("false")
                    print("i:", e_code[iter])

        # print("field_arr", field_arr)

        data = []
        for i in range(len(e_code)):
            # print(f"Error code for field '{field}': {error_code}")
            data.append({e_field[i]: [field_arr[i]]})
        # print("data", data)

        for i in range(len(non_e_field)):
            data.append({non_e_field[i]: ''})
        # print("data", data)

        def order_data(data):
            # Define the desired field order
            field_order = {
                "connection_name": 0,
                "user_name": 1,
                "password": 2,
                "account_id": 3,
                "host_id": 3,
                "port": 4,
                "schema_name": 4,
                "database_name": 5,
                "service_name_or_SID": 5,
                "warehouse_id": 6,
                "role": 7,
                "connection_type": 8,
                "auth_type": 9,
                "body" : 10,
                "auth_url": 11,
                "user_id": 12,
                "data_enpoint_url": 13,
                "method": 14,
            }

            # Sort the data based on the field order
            sorted_data = sorted(data, key=lambda item: field_order.get(
                list(item.keys())[0], float('inf')))

            return sorted_data

        # Order the data
        ordered_data = order_data(data)

        # Print the ordered data
        print("ordered_data",ordered_data)

        return Response(ordered_data, status=status.HTTP_404_NOT_FOUND)

# UPDATE
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def upd_rb_connect_definition_table(request, id):
    item = rb_connect_definition_table.objects.get(id=id)
    # print(request.data)

    serializer = rb_connect_definition_table_serializer(
        instance=item, data=request.data)
    all_serializer_fields = list(serializer.fields.keys())

    # print("all_serializer_fields",all_serializer_fields)

    # Fields to exclude
    fields_to_exclude = ['id', 'created_by', 'last_updated_by', 'created_date']

    # Remove the excluded fields from the list of field names
    required_serializer_fields = [
        field for field in all_serializer_fields if field not in fields_to_exclude]

    # print("required_serializer_fields",required_serializer_fields)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        error_data = serializer.errors
        # print("error_data", error_data, len(error_data))
        e_code = []
        e_msg = []
        e_field = []
        # Iterate over each field's errors
        for field, error_list in error_data.items():
            for error_data in error_list:
                # Access the error code
                error_code = error_data.code
                e_code.append(error_code)
                e_msg.append(error_data)
                e_field.append(field)

        # print("e_code", e_code, "length", len(e_code))
        # print("e_msg", e_msg, "length", len(e_msg))
        # print("e_field", e_field, "length", len(e_field))

        # Remove the excluded fields from the list of field names
        non_e_field = [
            for_field for for_field in required_serializer_fields if for_field not in e_field]

        # print("non_e_field",non_e_field)

        data_warning = warnings.objects.filter(
            error_code__in=e_code, error_from="Server"
        )
        serializer_warning = warnings_serializer(data_warning, many=True)
        # print("serializer_warning length", serializer_warning.data)

        # ! test validation on Backend level

        field_arr = []
        for iter in range(len(e_code)):
            for j in serializer_warning.data:
                # print("out : ", e_code[iter], j["error_code"])
                if e_code[iter] == j["error_code"]:
                    field_arr.append(
                        (j["error_msg"]).replace(
                            "%1", e_field[iter].replace("_", " "))
                    )
                    # print("true")
                    # print("j:", j["error_msg"])
                else:
                    print("false")
                    print("i:", e_code[iter])

        # print("field_arr", field_arr)

        data = []
        for i in range(len(e_code)):
            # print(f"Error code for field '{field}': {error_code}")
            data.append({e_field[i]: [field_arr[i]]})
        # print("data", data)

        for i in range(len(non_e_field)):
            data.append({non_e_field[i]: ''})
        # print("data", data)

        def order_data(data):
            # Define the desired field order
            field_order = {
                "connection_name": 0,
                "user_name": 1,
                "password": 2,
                "account_id": 3,
                "host_id": 3,
                "port": 4,
                "schema_name": 4,
                "database_name": 5,
                "service_name_or_SID": 5,
                "warehouse_id": 6,
                "role": 7,
                "connection_type": 8,
                "auth_type": 9,
                "body" : 10,
                "auth_url": 11,
                "user_id": 12,
                "data_enpoint_url": 13,
                "method": 14,
            }

            # Sort the data based on the field order
            sorted_data = sorted(data, key=lambda item: field_order.get(
                list(item.keys())[0], float('inf')))

            return sorted_data

        # Order the data
        ordered_data = order_data(data)

        # Print the ordered data
        # print("ordered_data",ordered_data)

        return Response(ordered_data, status=status.HTTP_404_NOT_FOUND)


# DELETE
@api_view(["PUT"])
# @permission_classes([IsAuthenticated])
def del_rb_connect_definition_table(request, id):
    item = rb_connect_definition_table.objects.get(id=id)
    data = request.data

    if item.delete_flag != data["delete_flag"]:
        item.delete_flag = data["delete_flag"]

    item.save()
    serializer = rb_connect_definition_table_serializer(item)
    return Response(serializer.data, status=status.HTTP_200_OK)





# *** Query Builder Restful Connect***

# # View all
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def get_rb_rest_connect_table(request, id=0):
#     if id == 0:
#         rb = rb_rest_connect_table.objects.filter(delete_flag="N")
#     else:
#         rb = rb_rest_connect_table.objects.filter(id=id)

#     serializer = rb_rest_connect_table_Serializer(rb, many=True)
#     return Response(serializer.data)

# # GET
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def get_range_rb_rest_connect_table(request, start, end):
#     pers_len = rb_rest_connect_table.objects.filter(delete_flag="N").count()
#     pers = rb_rest_connect_table.objects.filter(delete_flag="N")[start:end]
#     pers_csv_export = rb_rest_connect_table.objects.filter(delete_flag="N")
#     serializer = rb_rest_connect_table_Serializer(pers, many=True)
#     serializer_csv_export = rb_rest_connect_table_Serializer(pers_csv_export, many=True)
#     return Response(
#         {
#             "data": serializer.data,
#             "data_length": pers_len,
#             "csv_data": serializer_csv_export.data,
#         }
#     )

# # ADD
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def ins_rb_rest_connect_table(request):
#     data = {
#         "connection_name":request.data.get("connection_name"),
#         "connection_type":request.data.get("connection_type"),
#         "auth_type": request.data.get("auth_type"),
#         "auth_url": request.data.get("auth_url"),
#         "body": request.data.get("body"),
#         "user_id": request.data.get("user_id"),
#         "password": request.data.get("password"),
#         "data_enpoint_url": request.data.get("data_enpoint_url"),
#         "method": request.data.get("method"),
#         "created_by": request.data.get("created_by"),
#         "last_updated_by": request.data.get("last_updated_by"),
#     }

#     serializer = rb_rest_connect_table_Serializer(data=data)
    
#     all_serializer_fields = list(serializer.fields.keys())

#     # Fields to exclude
#     fields_to_exclude = ['id', 'created_by', 'last_updated_by', 'created_date']

#     # Remove the excluded fields from the list of field names
#     required_serializer_fields = [field for field in all_serializer_fields if field not in fields_to_exclude]

#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     else:
#         error_data = serializer.errors
#         # print("error_data", error_data, len(error_data))
#         e_code = []
#         e_msg = []
#         e_field = []
#         # Iterate over each field's errors
#         for field, error_list in error_data.items():
#             for error_data in error_list:
#                 # Access the error code
#                 error_code = error_data.code
#                 e_code.append(error_code)
#                 e_msg.append(error_data)
#                 e_field.append(field)

#         # Remove the excluded fields from the list of field names
#         non_e_field = [for_field for for_field in required_serializer_fields if for_field not in e_field]

#         # print("non_e_field",non_e_field)

#         data_warning = warnings.objects.filter(
#             error_code__in=e_code, error_from="Server"
#         )
#         serializer_warning = warnings_serializer(data_warning, many=True)
#         # print("serializer_warning length", serializer_warning.data)

#         # ! test validation on Backend level

#         field_arr = []
#         for iter in range(len(e_code)):
#             for j in serializer_warning.data:
#                 # print("out : ", e_code[iter], j["error_code"])
#                 if e_code[iter] == j["error_code"]:
#                     field_arr.append(
#                         (j["error_msg"]).replace("%1", e_field[iter].replace("_", " "))
#                     )
#                     # print("true")
#                     # print("j:", j["error_msg"])
#                 else:
#                     print("false")
#                     print("i:", e_code[iter])

#         # print("field_arr", field_arr)

#         data = []
#         for i in range(len(e_code)):
#             # print(f"Error code for field '{field}': {error_code}")
#             data.append({e_field[i]: [field_arr[i]]})
#         # print("data", data)

#         for i in range(len(non_e_field)):
#             data.append({non_e_field[i]: ''})
#         # print("data", data)

#         def order_data(data):
#             # Define the desired field order
#             field_order = {
#                 "connection_name": 0,
#                 "connection_type": 1,
#                 "auth_type": 2,
#                 "body" : 3,
#                 "auth_url": 4,
#                 "user_id": 5,
#                 "password": 6, 
#                 "data_enpoint_url": 7,
#                 "method": 8,
#             }

#             # Sort the data based on the field order
#             sorted_data = sorted(data, key=lambda item: field_order.get(list(item.keys())[0], float('inf')))

#             return sorted_data
    
#         # Order the data
#         ordered_data = order_data(data)

#         # Print the ordered data
#         # print("ordered_data",ordered_data)

#         return Response(ordered_data, status=status.HTTP_404_NOT_FOUND)
    
# # UPDATE
# @api_view(["PUT"])
# @permission_classes([IsAuthenticated])
# def upd_rb_db_connect_definition_table(request, id):
#     item = rb_rest_connect_table.objects.get(id=id)

#     serializer = rb_rest_connect_table_Serializer(instance=item, data=request.data)
#     all_serializer_fields = list(serializer.fields.keys())

#     # Fields to exclude
#     fields_to_exclude = ['id', 'created_by', 'last_updated_by', 'created_date']

#     # Remove the excluded fields from the list of field names
#     required_serializer_fields = [field for field in all_serializer_fields if field not in fields_to_exclude]

#     # print("required_serializer_fields",required_serializer_fields)

#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     else:
#         error_data = serializer.errors
#         # print("error_data", error_data, len(error_data))
#         e_code = []
#         e_msg = []
#         e_field = []
#         # Iterate over each field's errors
#         for field, error_list in error_data.items():
#             for error_data in error_list:
#                 # Access the error code
#                 error_code = error_data.code
#                 e_code.append(error_code)
#                 e_msg.append(error_data)
#                 e_field.append(field)

#         # print("e_code", e_code, "length", len(e_code))
#         # print("e_msg", e_msg, "length", len(e_msg))
#         # print("e_field", e_field, "length", len(e_field))

#         # Remove the excluded fields from the list of field names
#         non_e_field = [for_field for for_field in required_serializer_fields if for_field not in e_field]

#         # print("non_e_field",non_e_field)

#         data_warning = warnings.objects.filter(
#             error_code__in=e_code, error_from="Server"
#         )
#         serializer_warning = warnings_serializer(data_warning, many=True)
#         # print("serializer_warning length", serializer_warning.data)

#         # ! test validation on Backend level

#         field_arr = []
#         for iter in range(len(e_code)):
#             for j in serializer_warning.data:
#                 # print("out : ", e_code[iter], j["error_code"])
#                 if e_code[iter] == j["error_code"]:
#                     field_arr.append(
#                         (j["error_msg"]).replace("%1", e_field[iter].replace("_", " "))
#                     )
#                     # print("true")
#                     # print("j:", j["error_msg"])
#                 else:
#                     print("false")
#                     print("i:", e_code[iter])

#         # print("field_arr", field_arr)

#         data = []
#         for i in range(len(e_code)):
#             # print(f"Error code for field '{field}': {error_code}")
#             data.append({e_field[i]: [field_arr[i]]})
#         # print("data", data)

#         for i in range(len(non_e_field)):
#             data.append({non_e_field[i]: ''})
#         # print("data", data)

#         def order_data(data):
#             # Define the desired field order
#             field_order = {
#                 "connection_name": 0,
#                 "connection_type": 1,
#                 "auth_type": 2,
#                 "body" : 3,
#                 "auth_url": 4,
#                 "user_id": 5,
#                 "password": 6, 
#                 "data_enpoint_url": 7,
#                 "method": 8,
#             }

#             # Sort the data based on the field order
#             sorted_data = sorted(data, key=lambda item: field_order.get(list(item.keys())[0], float('inf')))

#             return sorted_data
    
#         # Order the data
#         ordered_data = order_data(data)

#         # Print the ordered data
#         # print("ordered_data",ordered_data)

#         return Response(ordered_data, status=status.HTTP_404_NOT_FOUND)

# # DELETE
# @api_view(["PUT"])
# @permission_classes([IsAuthenticated])
# def del_rb_rest_connect_table(request, id):
#     item = rb_rest_connect_table.objects.get(id=id)
#     data = request.data

#     if item.delete_flag != data["delete_flag"]:
#         item.delete_flag = data["delete_flag"]

#     item.save()
#     serializer = rb_rest_connect_table_Serializer(item)
#     return Response(serializer.data, status=status.HTTP_200_OK)
