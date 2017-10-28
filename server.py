from flask import Flask, render_template
import os
import json
app = Flask(__name__)

# load our data dictionaries
with open('ranking.json') as f:
    ranking = json.load(f)
with open('time.json') as f:
    time = json.load(f)
with open('grade.json') as f:
    grade = json.load(f)
print('json loaded')

# load the course and build a dictionary of the form d: 'ECE 35' -> 'ece/35'
courses = sorted(ranking.keys())
url_dict = {i: '/' + '/'.join(i.lower().split(' ')) for i in courses} 
print('url_dict loaded')

# build a W3 CSS panel corresponding to the type of statement (relax/norm/warn)
def build_panel(code, dictionary):
    color = dictionary[code]['color']
    if color == 'red':
        panel_class = 'w3-container w3-pale-red w3-leftbar w3-border-red'
    elif color == 'green':
        panel_class = 'w3-container w3-pale-green w3-leftbar w3-border-green'
    else: 
        panel_class = 'w3-container w3-light-gray w3-leftbar w3-border-gray'

    panel = '<div class="' + panel_class + '">' + \
            '<h3>' + dictionary[code]['expected'] + '</h3>' + \
            '<p>' + dictionary[code]['statement'] + '</p>' + \
            '</div>'

    return panel

def build_time_panel(code):
    return build_panel(code, time)

def build_grade_panel(code):
    return build_panel(code, grade)
            
@app.route("/")
def hello():
    return render_template("home.html", url_dict=url_dict)

@app.route("/<dept>/<course>")
def welcome(dept, course):
    code = (dept + ' ' + course).upper()
    try:
        rank = ranking[code]
        
        time_panel = build_time_panel(code)
        grade_panel = build_grade_panel(code)
        
    except KeyError:
        return render_template('nodata.html', code=code)

    return render_template("report.html", url_dict=url_dict, 
                           code=code, rank=rank, time_panel=time_panel, 
                           grade_panel=grade_panel)

port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

