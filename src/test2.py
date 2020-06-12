import csv
import chardet    

import xlrd

fpath = r'C:\Users\Tuey\Desktop\datis1.xlsx'

workbook = xlrd.open_workbook(fpath)
sheet = workbook.sheet_by_index(0)
data = [ ]
for rowx in range(1,sheet.nrows):
    uniqueID = str(int(sheet.row_values(rowx)[1]))
    if uniqueID.startswith('86'):
        uniqueID = uniqueID[3:]
    elif uniqueID.startswith('11'):
        uniqueID = uniqueID[2:]
    print(uniqueID)

