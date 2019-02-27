from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.request import Request

from pyramid.view import view_config
import json
import psycopg2



def connect_db(your_name):
    conn = psycopg2.connect("dbname='odoo' user='odoo' host='127.0.0.1' password='odoo'")
    cur = conn.cursor()
    sql = "insert into test_db (user_name) values('" + your_name + "')"
    cur.execute(sql)
    cur.execute("""SELECT user_name from test_db""")
    rows = cur.fetchall()
    #for row in rows:
    #    print "   ", row[0]

    conn.commit()
    conn.close()


def hello_world(request):
    parameters = request.params.getall("your_name")
    print(parameters)
    connect_db(parameters[0])
    return Response('Hello World!')


def translate_project_task(request):
    print ('start it')
    parameters = request.params.getall("project_id")
    print (parameters)
    conn = psycopg2.connect("dbname='odoo' user='odoo' host='127.0.0.1' password='odoo'")
    cur = conn.cursor()
    if len(parameters) > 0:
        project_id = str(parameters[0])
        print(project_id)
        sql_query = """SELECT id, date_start, project_id, description, name, date_deadline,
        date_deadline::date - date_start::date as duration, parent_id from project_task
            where active=True and project_id=(select project_id from project_task where id= """ + project_id + " ) "
    else:
        sql_query = """SELECT id, date_start, project_id, description, name, date_deadline,date_deadline::date -
         date_start::date as duration, parent_id from project_task
            where active=True"""
    print(sql_query)
    cur.execute(sql_query)
    rows = cur.fetchall()
    data_result = {'data':[], 'links':[]}

    # data links:
    # "links":[
    #     {"id": 1, "source": 1, "target": 2, "type": "1"},
    #     {"id": 2, "source": 2, "target": 3, "type": "0"}
    # ]

    for row in rows:
        if 1 != 1:
            task_type = 'gantt.config.types.milestone'
            row_i = {'id':row[0], 'project_id':row[2], 'text':row[4], 'start_date':'{:%d-%m-%Y}'.format(row[1]),
                     'duration':row[6], 'milestone':task_type, 'parent':row[7]}
        else:
            row_i = {'id': row[0], 'project_id': row[2], 'text': row[4], 'start_date': '{:%d-%m-%Y}'.format(row[1]),
                     'duration': row[6], 'parent':row[7]}

        data_result['data'].append(row_i)

    #print data_result

    sql_query_link = "select id, source, target, type from project_link"
    cur.execute(sql_query_link)
    rows = cur.fetchall()
    for row in rows:
        row_i = {'id':row[0], 'source':row[1], 'target':row[2], 'type':row[3]}
        data_result['links'].append(row_i)

    #print data_result

    response = Response()
    response.headers = [('Content-Type', 'text/event-stream'), ('Access-Control-Allow-Origin', '*'),('Cache-Control',
                                                                                                     'no-cache')]
    response.text = json.dumps(data_result)
    response.content_type = 'application/json'
    return response
        # print "   ", row[0], row[1], row[2], row[3], row[4], row[5]


def update_task(request):
    print(request.json_body)
    p_id = request.json_body['id']
    date_start = request.json_body['date_start']
    date_end = request.json_body['date_end']
    print (date_start)
    date_start = date_start[:10]
    print(date_end)
    # duration = int(request.json_body['duration'])

    conn = psycopg2.connect("dbname='odoo' user='odoo' host='127.0.0.1' password='odoo'")
    cur = conn.cursor()
    sql_update = 'update project_task set date_start = to_date(\'%(date_start)s\', \'MM/DD/YYYY\'),' \
                 ' date_deadline=to_date(\'%(date_end)s\', \'MM/DD/YYYY\')  where id = %(id)s' \
                 % {'id': p_id, 'date_end':date_end, 'date_start': date_start}
    print (sql_update)
    cur.execute(sql_update)
    conn.commit()
    data_result = {'status': 'update task successed'}
    response = Response()
    response.headers = [('Content-Type', 'text/event-stream'), ('Access-Control-Allow-Origin', '*'),
                        ('Cache-Control', 'no-cache')]
    response.text = json.dumps(data_result)
    response.content_type = 'application/json'
    return response


def del_link(request):
    print(request.json_body)
    p_id = request.json_body['id']
    conn = psycopg2.connect("dbname='odoo' user='odoo' host='127.0.0.1' password='odoo'")
    cur = conn.cursor()
    sql_query = 'delete from project_link where id = %(id)s' %{'id':p_id}
    print (sql_query)
    cur.execute(sql_query)
    conn.commit()
    data_result = {'success': 'ok'}
    response = Response()
    response.headers = [('Content-Type', 'text/event-stream'), ('Access-Control-Allow-Origin', '*'),
                        ('Cache-Control', 'no-cache')]
    response.text = json.dumps(data_result)
    response.content_type = 'application/json'
    return response


def add_new_link(request):
    print(request.json_body)

    p_id = request.json_body['id']
    p_source = int(request.json_body['source'])
    p_target = int(request.json_body['target'])
    p_type = int(request.json_body['type'])

    conn = psycopg2.connect("dbname='odoo' user='odoo' host='127.0.0.1' password='odoo'")
    cur = conn.cursor()
    sql_query = 'insert into project_link(id, source, target, type) values(%(id)s, %(source)d, %(target)d, %(type)d)' % {"id":p_id, "source":p_source, "target":p_target, "type":p_type}
    print (sql_query)
    cur.execute(sql_query)
    conn.commit()
    data_result = {'success': 'ok'}
    response = Response()
    response.headers = [('Content-Type', 'text/event-stream'), ('Access-Control-Allow-Origin', '*'),
                        ('Cache-Control', 'no-cache')]
    response.text = json.dumps(data_result)
    response.content_type = 'application/json'
    return response

if __name__ == '__main__':
    with Configurator() as config:

        config.add_route('hello', '/hello')
        config.add_view(hello_world, route_name='hello')

        config.add_route('translate_project_task', '/translate_project_task')
        config.add_view(translate_project_task, route_name='translate_project_task', renderer='string')

        config.add_route('add_new_link', '/add_new_link')
        config.add_view(add_new_link, route_name='add_new_link', renderer='json')

        config.add_route('del_link', '/del_link')
        config.add_view(del_link, route_name='del_link', renderer='json')

        config.add_route('update_task', '/update_task')
        config.add_view(update_task, route_name='update_task', renderer='json')

        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
    # print translate_project_task()

    # connect_db('thai')
