import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import hashlib
import os
import cryptography
from cryptography.fernet import Fernet
from math import pow

class database:

    def __init__(self, purge = False):

        # Grab information from the configuration file
        self.database       = 'db'
        self.host           = '127.0.0.1'
        self.user           = 'master'
        self.port           = 3306
        self.password       = 'master'
        self.tables         = ['users', 'boards', 'contributors', 'tasks']
        
        # NEW IN HW 3-----------------------------------------------------------------
        self.encryption     =  {   'oneway': {'salt' : b'averysaltysailortookalongwalkoffashortbridge',
                                                 'n' : int(pow(2,5)),
                                                 'r' : 9,
                                                 'p' : 1
                                             },
                                'reversible': { 'key' : '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE='}
                                }
        #-----------------------------------------------------------------------------

    def query(self, query = "SELECT * FROM users", parameters = None):

        cnx = mysql.connector.connect(host     = self.host,
                                      user     = self.user,
                                      password = self.password,
                                      port     = self.port,
                                      database = self.database,
                                      charset  = 'latin1'
                                     )


        if parameters is not None:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query, parameters)
        else:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query)

        # Fetch one result
        row = cur.fetchall()
        cnx.commit()

        if "INSERT" in query:
            cur.execute("SELECT LAST_INSERT_ID()")
            row = cur.fetchall()
            cnx.commit()
        cur.close()
        cnx.close()
        return row

    def createTables(self, purge=False, data_path = 'flask_app/database/'):
        ''' FILL ME IN WITH CODE THAT CREATES YOUR DATABASE TABLES.'''

        #should be in order or creation - this matters if you are using forign keys.
         
        if purge:
            for table in self.tables[::-1]:
                self.query(f"""DROP TABLE IF EXISTS {table}""")
            
        # Execute all SQL queries in the /database/create_tables directory.
        for table in self.tables:
            
            #Create each table using the .sql file in /database/create_tables directory.
            with open(data_path + f"create_tables/{table}.sql") as read_file:
                create_statement = read_file.read()
            self.query(create_statement)

            # Import the initial data
            try:
                params = []
                with open(data_path + f"initial_data/{table}.csv") as read_file:
                    scsv = read_file.read()            
                for row in csv.reader(StringIO(scsv), delimiter=','):
                    params.append(row)
            
                # Insert the data
                cols = params[0]; params = params[1:] 
                self.insertRows(table = table,  columns = cols, parameters = params)
            except:
                print('no initial data')
            
    def insertRows(self, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):
    
        # Check if there are multiple rows present in the parameters
        has_multiple_rows = any(isinstance(el, list) for el in parameters)
        keys, values      = ','.join(columns), ','.join(['%s' for x in columns])
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO {table} ({keys}) VALUES """
        if has_multiple_rows:
            for p in parameters:
                query += f"""({values}),"""
            query     = query[:-1] 
            parameters = list(itertools.chain(*parameters))
        else:
            query += f"""({values}) """                      
        
        insert_id = self.query(query,parameters)[0]['LAST_INSERT_ID()']         
        return insert_id
    
    def getResumeData(self):
    
        # queries to gather data from each table
        inst_query = """
            SELECT inst_id, type, name, department, address, city, state, zip
            FROM institutions"""
        pos_query = """
            SELECT position_id, inst_id, title, responsibilities, start_date, end_date
            FROM positions"""
        exp_query = """
            SELECT experience_id, position_id, name, description, hyperlink, start_date, end_date
            FROM experiences"""
        skills_query = """
            SELECT skill_id, experience_id, name, skill_level
            FROM skills"""
        
        #gather data from each table
        inst_data = self.query(inst_query)
        pos_data = self.query(pos_query)
        exp_data = self.query(exp_query)
        skills_data = self.query(skills_query)

        #initialize resume_data
        resume_data = {}

        #gather institutions data and place into resume_data
        for inst in inst_data:
            inst_id = inst['inst_id']
            if inst_id not in resume_data:
                resume_data[inst_id] = {
                    'address': inst['address'],
                    'city': inst['city'],
                    'state': inst['state'],
                    'type': inst['type'],
                    'zip': inst['zip'],
                    'department': inst['department'],
                    'name': inst['name'],
                    'positions': {}
                }

        #gather positions data and place into resume_data
        for pos in pos_data:
            inst_id = pos['inst_id']
            position_id = pos['position_id']
            if inst_id in resume_data:
                resume_data[inst_id]['positions'][position_id] = {
                    'end_date': pos['end_date'],
                    'responsibilities': pos['responsibilities'],
                    'start_date': pos['start_date'],
                    'title': pos['title'],
                    'experiences': {}
                }

        #gather experience_data and place into resume_data
        for exp in exp_data:
            position_id = exp['position_id']
            experience_id = exp['experience_id']
            for inst_id, inst_info in resume_data.items():
                if position_id in inst_info['positions']:
                    inst_info['positions'][position_id]['experiences'][experience_id] = {
                        'description': exp['description'],
                        'end_date': exp['end_date'],
                        'hyperlink': exp['hyperlink'],
                        'name': exp['name'],
                        'skills': {},
                        'start_date': exp['start_date']
                    }
        #gather skills data annd place into resume_data
        for skill in skills_data:
            experience_id = skill['experience_id']
            skill_id = skill['skill_id']
            for inst_id, inst_info in resume_data.items():
                for position_info in inst_info['positions'].values():
                    if experience_id in position_info['experiences']:
                        position_info['experiences'][experience_id]['skills'][skill_id] = {
                            'name': skill['name'],
                            'skill_level': skill['skill_level']
                        }
        return resume_data

#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
    def createUser(self, email='me@email.com', password='password', role='user'):

        #initial user length
        initial_query = """SELECT * FROM users"""
        initial_users = self.query(initial_query)
        
        #check if email already in database
        emails_query = """ SELECT email FROM users"""
        emails = self.query(emails_query) 
        for x in emails:
            if x['email'] == email:
                return {'success': 0}
        
        #encrypt password
        password = self.onewayEncrypt(password)
        columns = ['role','email', 'password']
        #how to auto increment user_id here?
        parameters = [role, email, password]

        # get keys and values for the row
        keys = ','.join(columns)
        values = ','.join(['%s' for x in columns])
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO users ({keys}) VALUES ({values}) """                  
        insert_id = self.query(query,parameters)

        #check if users length increased
        post_query = """SELECT * FROM users"""
        post_users = self.query(initial_query)


        if len(post_users) > len(initial_users):
            return {'success': 1}
        else:
            return {'success': 0}

    def authenticate(self, email='me@email.com', password='password'):
        users_query = """ SELECT * from users"""
        users = self.query(users_query)
        for user in users:
            if (user['email'] == email) and (user['password'] == self.onewayEncrypt(password)):
                return {'success': 1}
        return {'success': 0}
    
    def half_authenticate(self, email="me@email.com"):
        users_query = """ SELECT * from users"""
        users = self.query(users_query)
        for user in users:
            if (user['email'] == email):
                return {'success': 1}
        return {'success': 0}

    def onewayEncrypt(self, string):
        encrypted_string = hashlib.scrypt(string.encode('utf-8'),
                                          salt = self.encryption['oneway']['salt'],
                                          n    = self.encryption['oneway']['n'],
                                          r    = self.encryption['oneway']['r'],
                                          p    = self.encryption['oneway']['p']
                                          ).hex()
        return encrypted_string


    def reversibleEncrypt(self, type, message):
        fernet = Fernet(self.encryption['reversible']['key'])
        
        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message

#######################################################################################
# BOARD RELATED
#######################################################################################
    def createBoard(self, name='name', emails=['me@gmail.com']):
            
            #initial length of boards
            initial_query = """SELECT * FROM boards"""
            initial_dat = self.query(initial_query)

            #make column names and parameters for boards
            columns_boards = ['name', 'owner_email']
            parameters_boards = [name, emails[0]]

            # get keys and values for the row
            keys_boards = ','.join(columns_boards)
            values = ','.join(['%s' for x in columns_boards])
            
            # Construct the query we will execute to insert the row(s)
            query_boards = f"""INSERT IGNORE INTO boards ({keys_boards}) VALUES ({values}) """  
            insert_board = self.query(query_boards,parameters_boards)

            #find the board_id of the one created
            board_query = f"""SELECT board_id FROM boards WHERE name='{name}' AND owner_email='{emails[0]}'"""
            board_id = self.query(board_query)
            
            #create contributors for the board
            for i in emails:
                #make column names and parameters for boards
                columns_contributors = ['board_id', 'user_email', 'role']
                parameters_contributors = [board_id[0]['board_id'], i, 'editor']

                # get keys and values for the row
                keys_contributors = ','.join(columns_contributors)
                values = ','.join(['%s' for x in columns_contributors])

                # Construct the query we will execute to insert the row(s)
                query_contributors = f"""INSERT IGNORE INTO contributors ({keys_contributors}) VALUES ({values}) """
                insert_contributor = self.query(query_contributors,parameters_contributors) 

            #check if boards length increased
            post_board = """SELECT * FROM boards"""
            post_boards = self.query(post_board)


            if len(post_boards) > len(initial_dat):
                return {'success': 1, 'board_id': board_id[0]['board_id']}
            else:
                return {'success': 0}
    
    def getBoardData(self, board_id):
        board_query = f"""SELECT * FROM boards WHERE board_id= {board_id}"""
        board_dat = self.query(board_query);
        return board_dat
    
#######################################################################################
# TASK RELATED
#######################################################################################
    def createTask(self, board_id, description="task description", category="todo"):
        #initial length of tasks
        initial_query = """SELECT * FROM tasks"""
        initial_dat = self.query(initial_query)

        #make column names and parameters for boards
        columns = ['board_id', 'description', 'category']
        parameters = [board_id, description, category]

        # get keys and values for the row
        keys = ','.join(columns)
        values = ','.join(['%s' for x in columns])

        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO tasks ({keys}) VALUES ({values}) """  
        insert = self.query(query,parameters)
        task_id = insert[0]['LAST_INSERT_ID()']

        #check if tasks length increased
        post_task = """SELECT * FROM tasks"""
        post_tasks = self.query(post_task)

        if len(post_tasks) > len(initial_dat):
            return task_id
        else:
            return {'success': 0}
        
    def getTaskData(self, board_id):
        task_query = f"""SELECT * FROM tasks WHERE board_id = {board_id}"""
        tasks = self.query(task_query)
        print(tasks)
        return tasks
    
    def editTask(self, task_id, description):
        task_query = f"""UPDATE tasks SET description='{description}' WHERE task_id={task_id}"""
        print(task_query)
        task_edit = self.query(task_query)
        return {'success':1}
    
    def moveTask(self, task_id, category):
        task_query = f"""UPDATE tasks SET category='{category}' WHERE task_id={task_id}"""
        print(task_query)
        task_edit = self.query(task_query)
        return {'success':1}
    
    def deleteTask(self, task_id):
        task_query = f"""DELETE FROM tasks WHERE task_id={task_id}""" 
        task_delete = self.query(task_query)
        return {'success': 1}
    
#######################################################################################
# EXISTING BOARD RELATED
#######################################################################################
    def existing_data(self, user='me@email.com'):
        all_data = []
        user_query = f"""SELECT board_id FROM contributors WHERE user_email='{user}'"""
        user_dat = self.query(user_query)
        for board_id in user_dat:
            board_name_query = f"""SELECT name FROM boards WHERE board_id='{board_id['board_id']}'"""
            board_name = self.query(board_name_query)
            data_d = {'board_id': board_id['board_id'], 'board_name':board_name[0]['name']}
            all_data.append(data_d)
        return all_data
