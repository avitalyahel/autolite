import json
import subprocess


g_root_url = '/'

def set_root_url(root: str):
    global g_root_url
    g_root_url = root


HTML_HEAD = '''<html>
<head>
<style type="text/css">
tr.Record:hover {
    color: Blue;
    cursor: pointer;
}
h2 {
    color: DodgerBlue;
    text-align: center;
    font-family: Trebuchet MS;
    cursor: pointer
}
</style>
<script type="text/javascript">
function loadUrl(newLocation)
{
    window.location.href = newLocation;
    return false;
}
</script>
</head>
<body style="text-align: center; font-family: Sans-serif">
<h2>autolite</h2>
'''

HTML_TAIL = '''
</body>
</html>'''

TABLE = '''
<table width="100" cellspacing="5" align="center">
<tr>{head}</tr>
{rows}
</table>
'''

TH = '<th style="text-align:left">{}</th>'
TR = '<tr class="{cls}" {onclick}>{cells}</tr>'
TD = '<td nowrap style="vertical-align:top">{}</td>'
A = '<a href="{val}">{val}</a>'


def html_table(data: [dict] = [], columns: [str] = [], click_url: str = '/') -> str:
    return TABLE.format(
        head=html_table_head(columns),
        rows='\n'.join(html_table_row(row, columns, onclick='onclick="loadUrl(\'{}\')"'.format(click_url + row['name'])) for row in data),
    )


def html_table_head(columns: [str]) -> str:
    return ''.join(TH.format(col.title()) for col in columns)


def html_table_row(row: dict, columns: [str], onclick: str = "") -> str:
    return TR.format(
        cls='' if len(columns) == 2 else 'Record',
        onclick=onclick,
        cells=''.join(TD.format(A.format(val=row[key]) if row[key].startswith('http') else row[key]) for key in columns),
    )


def html_record(data: dict = {}, fields: [str] = []) -> str:
    columns = ['field', 'value']
    return TABLE.format(
        head=html_table_head(columns),
        rows='\n'.join(html_table_row(dict(field=field, value=data[field]), columns)
                       for field in fields if field in data),
    )


# HTML


def index() -> str:
    return HTML_HEAD + '''
<p><a href="{root}tasks">Tasks</a> | <a href="{root}systems">Systems</a></p>
'''.format(root=g_root_url) + \
    html_table() + \
    HTML_TAIL


def html_tasks() -> str:
    data = json.loads(subprocess.getoutput('autolite task list -J'))
    columns = 'name parent schedule state resources last'.split(' ')
    return HTML_HEAD + '''
<p><b>Tasks</b> | <a href="{root}systems">Systems</a></p>
'''.format(root=g_root_url) + \
    html_table(data, columns, click_url='/tasks/') + \
    HTML_TAIL


def html_task(name: str = '') -> str:
    tasks = json.loads(subprocess.getoutput('autolite task list {} -J'.format(name)))
    task = tasks[0] if tasks else dict()
    fields = 'name parent schedule state condition command resources log email last'.split(' ')
    return HTML_HEAD + '''
<p><a href="{root}tasks">Tasks</a> | <a href="{root}systems">Systems</a></p>
'''.format(root=g_root_url) + \
    html_record(task, fields) + \
    HTML_TAIL


def html_systems() -> str:
    data = json.loads(subprocess.getoutput('autolite system list -J'))
    columns = 'name user comment'.split(' ')
    return HTML_HEAD + '''
<p><a href="{root}tasks">Tasks</a> | <b>Systems</b></p>
'''.format(root=g_root_url) + \
    html_table(data, columns, click_url='/systems/') + \
    HTML_TAIL


def html_system(name: str = '') -> str:
    systems = json.loads(subprocess.getoutput('autolite system list {} -J'.format(name)))
    system = systems[0] if systems else dict()
    fields = 'name ip user comment installer cleaner monitor config'.split(' ')
    return HTML_HEAD + '''
<p><a href="{root}tasks">Tasks</a> | <a href="{root}systems">Systems</a></p>
'''.format(root=g_root_url) + \
    html_record(system, fields) + \
    HTML_TAIL


# REST API


def get_tasks(name: str = '') -> dict:
    data = json.loads(subprocess.getoutput('autolite task list {} -J'.format(name)))
    return data[0] if len(data) == 1 else data


def get_systems(name: str = '') -> dict:
    data = json.loads(subprocess.getoutput('autolite system list {} -J'.format(name)))
    return data[0] if len(data) == 1 else data
