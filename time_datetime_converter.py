#Модуль переводит дату формата "time" в "datetime".

import time, datetime, os

def convert_to_datetime (date):
    date_year = str(date)[20]+str(date)[21]+str(date)[22]+str(date)[23]
    date_month = str(date)[4]+str(date)[5]+str(date)[6]
    date_day = str(date)[8]+str(date)[9]
    
    
    if date_month == 'Jan' :
     date_month = 1;
    elif date_month == 'Feb':
     date_month = 2;
    elif date_month == 'Mar':
     date_month = 3;
    elif date_month == 'Apr':
     date_month = 4;
    elif date_month == 'May':
     date_month = 5;    
    elif date_month == 'Jun':
     date_month = 6;
    elif date_month == 'Jul':
     date_month = 7;
    elif date_month == 'Aug':
     date_month = 8;
    elif date_month == 'Sep':
     date_month = 9;
    elif date_month == 'Oct':
     date_month = 10;
    elif date_month == 'Nov':
     date_month = 11;
    elif date_month == 'Dec':
     date_month = 12;
    
    return datetime.date(int(date_year), int(date_month), int(date_day))





    
