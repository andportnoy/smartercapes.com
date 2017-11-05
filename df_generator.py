import pandas as pd
from statsmodels.stats.proportion import proportion_confint as ci

df0 = pd.read_html('cape.htm')
df0[0].to_csv('cape.csv')
df = pd.read_csv('cape.csv', index_col = 0)

# Only using data from past 2 years to accurately reflect current courses
df = df[df.Term.isin(['S317', 'S217', 'S117', 'SP17', 'WI17', 'FA16', 'S316', 'S216', 'S116', 'SP16', 'WI16', 'FA15'])]
df = (df[['Instructor', 'Course', 'Evals Made', 'Rcmnd Instr', 'Study Hrs/wk', 'Avg Grade Expected', 'Avg Grade Received']])
df.columns = ['instr', 'course', 'evals', 'rcmnd', 'time', 'gradeE', 'gradeR']

# Remove all classes with no evals/grades
df1 = df.drop(df[df.isnull().any(axis = 1)].index, axis = 0)

df1.loc[:, 'rcmnd'] = df1.rcmnd.str.rstrip(' %').astype('float') / 100
df1.loc[:, 'weighted_evals'] = (df1.evals * df1.rcmnd).round().astype('int')
df1.loc[:, 'course'] = df1.course.str.split(' - ').apply(lambda x: x[0])

# Generate dataframe for ranking of profs
gb_ranking = df1.groupby(['course', 'instr']).sum()
gb_ranking.loc[:, 'lower'], gb_ranking.loc[:, 'upper'] = ci(gb_ranking.weighted_evals, gb_ranking.evals, method='wilson')
gb_ranking = gb_ranking.loc[:, ['lower', 'upper']]
gb_ranking = gb_ranking.sort_values('lower', ascending = False).swaplevel(0,1).sort_index(level=1, sort_remaining=False).swaplevel(0,1)

# Generate dataframe for average time commitment
gb_time = df1[['course', 'time']].groupby('course').mean().round(2)

# Generate dataframe for grades
gb_grade = df1[['course', 'gradeE', 'gradeR']]
# Convert grade to float containing gpa value
gb_grade.loc[:, 'gradeE'] = gb_grade.gradeE.str.split('(').apply(lambda x: x[1])
gb_grade.loc[:, 'gradeR'] = gb_grade.gradeR.str.split('(').apply(lambda x: x[1])
gb_grade.loc[:, 'gradeE'] = gb_grade.gradeE.str.rstrip(')')
gb_grade.loc[:, 'gradeR'] = gb_grade.gradeR.str.rstrip(')')
gb_grade[['gradeE', 'gradeR']] = gb_grade[['gradeE', 'gradeR']].apply(pd.to_numeric)
gb_grade.loc[:, 'diff'] = gb_grade.gradeR - gb_grade.gradeE
