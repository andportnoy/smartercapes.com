import pandas as pd
from natsort import natsorted
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from statsmodels.stats.proportion import proportion_confint as ci

CAPEURL = 'https://cape.ucsd.edu/responses/Results.aspx'
CAPEDUMPURL = 'https://cape.ucsd.edu/responses/Results.aspx?Name=%2C'
CAPETITLE = 'Course And Professor Evaluations (CAPE)'
def get_raw_cape_dataframe():

    # launch browser using Selenium, need to have Firefox installed
    print('Opening a browser window...')
    driver = webdriver.Firefox()
    print('Browser window open, loading the page...')

    # get the page that lists all the data, first try
    driver.get(CAPEURL)
    print('Please enter credentials...')

    # wait until SSO credentials are entered
    wait = WebDriverWait(driver, 60)
    element = wait.until(expected_conditions.title_contains(CAPETITLE))

    # get the page that lists all the data
    # (%2C is the comma, drops all the data since every professor name has it)
    driver.get(CAPEDUMPURL)

    # read in the dataset from the html file
    df = pd.read_html(driver.page_source)[0]
    print('Dataset parsed, closing browser window.')

    # destroy driver instance
    driver.quit()

    return df


def get_clean_cape_dataframe(raw_cape_dataframe, terms):

    df = raw_cape_dataframe

    # only looking at evaluations from 15/16 and 16/17
    df = df[df.Term.isin(terms)]

    # subset the columns we need
    df = df[['Instructor', 'Course', 'Term', 'Evals Made', 'Rcmnd Class',
             'Rcmnd Instr', 'Study Hrs/wk', 'Avg Grade Expected',
             'Avg Grade Received']]

    # rename the columns for convenience
    df = df.rename(columns={
        'Instructor': 'instr', 'Course': 'course', 'Term': 'term',
        'Evals Made': 'evals', 'Rcmnd Class': 'rcmnd_class',
        'Rcmnd Instr': 'rcmnd_instr', 'Study Hrs/wk': 'time',
        'Avg Grade Expected': 'grade_expected',
        'Avg Grade Received': 'grade_actual'
    })

    # drop rows that have data missing
    df = df.dropna()

    # only need the courses which hade at least one evaluation made
    df = df[df['evals'] != 0]

    # split to get the dept + course code
    df.loc[:, 'course'] = df.course.str.split(' - ').apply(lambda x: x[0])

    # convert the recommendation percentages to float values
    # and resize to be in the interval [0, 1]:
    df.loc[:, 'rcmnd_instr'] = (df.rcmnd_instr
                                  .str.rstrip(' %')
                                  .astype('float')) / 100

    df.loc[:, 'rcmnd_class'] = (df.rcmnd_class
                                  .str.rstrip(' %')
                                  .astype('float')) / 100

    """We create a "weighted evals" column which contains the recommendation
    percentage multiplied by the number of evals, yielding the approximate
    number of positive recommendations. We round them to obtain integer values.
    The exact numbers are available for every course, but it would require
    scraping a lot of pages.  Maybe in the next iteration."""

    df['class_weighted_evals'] = ((df.evals * df.rcmnd_class).round()
                                                             .astype('int'))
    df['instr_weighted_evals'] = ((df.evals * df.rcmnd_instr).round()
                                                             .astype('int'))

    df['letter_expected'] = (df.grade_expected.str.split('(')
                                              .apply(lambda x: x[0]))
    df['gpa_expected'] = (df.grade_expected.str.split('(')
                                           .apply(lambda x: x[-1])
                                           .str.rstrip(')')
                                           .astype('float'))

    df['letter_actual'] = (df.grade_actual.str.split('(')
                                          .apply(lambda x: x[0]))
    df['gpa_actual'] = (df.grade_actual.str.split('(')
                                       .apply(lambda x: x[-1])
                                       .str.rstrip(')')
                                       .astype('float'))

    df = df.drop(['grade_expected', 'grade_actual'], axis=1)

    # set and reset index to build an incremental index that starts at 0
    df = df.set_index('instr').reset_index()

    return df


def get_prof_ranking_dictionary(df):

    df = (df[['instr', 'course', 'evals', 'instr_weighted_evals']])

    gb = df.groupby(['course', 'instr']).sum()

    gb.loc[:, 'lower'], gb.loc[:, 'upper'] = ci(gb.instr_weighted_evals,
                                                gb.evals, method='wilson')

    # populate the dictionary
    ranking = {}
    for course, instr in gb.index:
        professors_sorted = gb.loc[course].sort_values(by='lower',
                                                       ascending=False)
        ranking[course] = list(professors_sorted.index)

    return ranking


def get_time_dictionary(df):

    # subset the columns we need
    df = df[['course', 'time']]

    # groupby to get average time for course and round to 2 decimal places
    gb = df[['time', 'course']].groupby('course').mean().round(2)

    # average time spent for all courses
    average = float(gb.mean())

    # standard deviation of time spent for all courses
    sd = float(gb.std())

    # build the deviation column
    gb['dev'] = gb - average

    # warning statements
    warning = (
        'This course will take more time outside of class than average.'
    )
    normal = (
        'This course will take an average amount of time outside of class.'
    )
    relax = (
        'This course might take less time outside of class than average.'
    )

    def get_statement_and_color(dev, sd):
        if (dev > sd):
            statement = warning
            color = 'red'
        elif (abs(dev) < sd):
            statement = normal
            color = 'black'
        else:
            statement = relax
            color = 'green'
        return statement, color

    time = {}
    for course in gb.index:
        statement, color = get_statement_and_color(gb.loc[course, 'dev'], sd)
        time[course] = {'expected': str(float(gb.loc[course, 'time'])),
                        'statement': statement, 'color': color}

    return time


def get_grade_dictionary(df):

    # subset the columns we need
    df = df[['course', 'gpa_expected', 'gpa_actual']]

    # groupby to get the mean grade and round to 2 decimal places
    gb = df.groupby('course').mean().round(2)
    gb['dev'] = gb.gpa_actual - gb.gpa_expected

    # warning statements
    warning = (
        'Students tend to get lower grades than they expect for this course.'
    )
    normal = (
        'Students tend to get the grade they expect for this course.'
    )
    relax = (
        'Students tend to get higher grades than they expect for this course.'
    )

    def GPA_val_to_grade(val):
        if val == 4.0:
            grade = 'A'
        elif val >= 3.7:
            grade = 'A-'
        elif val >= 3.3:
            grade = 'B+'
        elif val >= 3.0:
            grade = 'B'
        elif val >= 2.7:
            grade = 'B-'
        elif val >= 2.3:
            grade = 'C+'
        elif val >= 2.0:
            grade = 'C'
        elif val >= 1.7:
            grade = 'C-'
        elif val >= 1.0:
            grade = 'D'
        return grade

    def get_statement_and_color(dev):
        if dev > 0.4:
            color = 'green'
            statement = relax
        elif dev < -0.4:
            color = 'red'
            statement = warning
        else:
            color = 'black'
            statement = normal

        return statement, color

    grade = {}
    for course in gb.index:
        statement, color = get_statement_and_color(gb.loc[course, 'dev'])
        grade[course] = {
            'expected': GPA_val_to_grade(gb.loc[course, 'gpa_actual']),
            'color': color,
            'statement': statement
        }

    return grade


def get_depts_and_courses_dictionary(df):

    df = (df.course.str.split(expand=True)
            .rename(columns={0: 'dept', 1: 'course'})
            .drop_duplicates())

    depts = natsorted(df.dept.unique())

    df = df.set_index(['dept', 'course']).sort_index()

    depts_and_courses = {dept: natsorted(df.loc[dept].index) for dept in depts}

    return depts_and_courses
