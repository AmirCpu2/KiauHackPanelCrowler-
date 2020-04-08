from bs4 import BeautifulSoup
from lxml import html
import pandas as pd
import requests
import json
import time
import csv
import sys
import re
import os

#---------------------InitializeValue--------------------------
url                 = 'http://edu.kiau.ac.ir'
user                = ''
pasw                = ''
page                = 1
table               = []
cookies             = ''
sessionId 	        = ''
courseList          = []
tableCource         = []
courseTable         = []
captchaCode         = []
SubjectCorse        = ''
sessionIdHistory    = []

payload = {
"__EVENTTARGET": '' ,
"__EVENTARGUMENT": '' ,
"__VIEWSTATE": '' ,
"__VIEWSTATEGENERATOR": '' ,
"__EVENTVALIDATION": '' ,
"txtUserName": '' ,
"txtPassword": '' ,
"texttasvir": captchaCode ,
"LoginButton0":"ورود دانشجو"
}

payloadTable = {
"ctl00$ScriptManager1": 'ctl00$UpdatePanel1|ctl00$ContentPlaceHolder1$btnSave4' ,
"ctl00$ContentPlaceHolder1$a1": "RadioButton1",
"ctl00$ContentPlaceHolder1$TextBox1": "",
"__EVENTTARGET": '' ,
"__EVENTARGUMENT": '' ,
"__LASTFOCUS": '',
"__VIEWSTATE": '' ,
"__VIEWSTATEGENERATOR": '' ,
"__VIEWSTATEENCRYPTED": '',
"__EVENTVALIDATION": '' ,
"__ASYNCPOST": True,
"ctl00$ContentPlaceHolder1$btnSave4": " جــســتجــوی دروس"
}

# --------------------Functions---------------------

def ocr_space_file(filename, overlay=False, api_key='55c76e3c7d88957', language='eng'):
    """ OCR.space API request with local file.
        Python3.5 - not tested on 2.7
    :param filename: Your file path & name.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    payload = {'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload,
                          )
    return r.content.decode()

    """ OCR.space API request with remote file.
        Python3.5 - not tested on 2.7
    :param url: Image url.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    payload = {'url': url,
               'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               }
    r = requests.post('https://api.ocr.space/parse/image',
                      data=payload,
                      )
    return r.content.decode()

def GetValueById(object,element,id):
	try:
		return object.xpath('//{}[@id="{}"]/@value'.format(element,id))[0]
	except:
		return ''

def GetValueByName(object,element,name):
	try:
		return object.xpath('//{}[@name="{}"]/@value'.format(element,id))[0]
	except:
		return ''

def InitializeValue():
    global user, pasw
    # Get Value And Settion Temp
    BasePage = requests.get(url+"/login.aspx")
    sessionId = BasePage.cookies.get('ASP.NET_SessionId')
    sessionIdHistory.append(sessionId)
    tree = html.fromstring(BasePage.content)
    payload['__VIEWSTATE'] = GetValueById(tree,'input','__VIEWSTATE')
    payload['__VIEWSTATEGENERATOR'] = GetValueById(tree,'input','__VIEWSTATEGENERATOR')
    payload["txtUserName"] = user
    payload["txtPassword"] = pasw
    payload['__EVENTTARGET'] = GetValueById(tree,'input','__EVENTTARGET')
    payload['__EVENTARGUMENT'] = GetValueById(tree,'input','__EVENTARGUMENT')
    payload['__EVENTVALIDATION'] = GetValueById(tree,'input','__EVENTVALIDATION')

def GetNewSession():
    global cookies
    InitializeValue()
    GetNewCapcha()
    cookies = dict({'ASP.NET_SessionId':str(sessionIdHistory[-1])})
    requests.post(url+"/login.aspx",data=payload,cookies=cookies).cookies

def GetNewCapcha():
	try:
		cookiesTemp = dict({'ASP.NET_SessionId':str(sessionIdHistory[-1])})
		r = requests.get(url+"/captcha.aspx",cookies=cookiesTemp)
		f=open('yourcaptcha.png','wb')
		f.write(r.content)
		f.close()
		time.sleep(2)
		test_file = ocr_space_file(filename='yourcaptcha.png' ,language='pol').replace('false','False')
		captchaCode.append( eval(test_file)["ParsedResults"][0]["ParsedText"] )
		payload['texttasvir'] = str(int(captchaCode[-1]))
	except:
		GetNewCapcha()

def SetPayloadList(object,page):
	# Get Value And Settion Temp
	tree = html.fromstring(object.content)
	payloadTable['__VIEWSTATE'] = GetValueById(tree,'input','__VIEWSTATE')
	payloadTable['__VIEWSTATEGENERATOR'] = GetValueById(tree,'input','__VIEWSTATEGENERATOR')
	payloadTable['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$grdCourseList'
	payloadTable['__EVENTARGUMENT'] = 'Page${}'.format(page)
	payloadTable['__EVENTVALIDATION'] = GetValueById(tree,'input','__EVENTVALIDATION')
	# payloadTable['ctl00$ContentPlaceHolder1$btnSave4'] = GetValueById(tree,'input','ctl00_ContentPlaceHolder1_btnSave4')
	payloadTable['ctl00$ScriptManager1'] = 'ctl00$UpdatePanel1|ctl00$ContentPlaceHolder1$grdCourseList'

def SaveTable (DataTable):
    
   # Open File And set mode Write
    with open('KiauTables.csv', 'w',encoding='utf-8', newline='') as csvfile:
        
        # Head
        fieldnames = ['مشخصه', 'نام درس', 'مقطع کلاس', 'نظری', 'نوع عملی', 'نوع عملی', 'جنسیت', 'گروه کلاس', 
        'باقي مانده', 'ساعت کلاس', 'ساعت امتحان', 'ت امتحان', 'نام استاد', 'گروه بندی']
        
        # Config head
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write Head
        writer.writeheader()
        
        for row in DataTable:
            # Write Row
            try:
                writer.writerow({
                    fieldnames[0]: row[0],
                    fieldnames[1]: row[1],
                    fieldnames[2]: row[2],
                    fieldnames[3]: row[3],
                    fieldnames[4]: row[4],
                    fieldnames[5]: row[5],
                    fieldnames[6]: row[6],
                    fieldnames[7]: row[7],
                    fieldnames[8]: row[8], 
                    fieldnames[9]: row[9], 
                    fieldnames[10]: row[10],
                    fieldnames[11]: row[11], 
                    fieldnames[12]: row[12], 
                    fieldnames[13]: row[13] })
            except:
                pass

def parsTable(soup):
    # Get row
    rows = soup.find_all('tr', {'class':'GridViewRow'})
    
    rows.extend(soup.find_all('tr', {'class':'GridViewAlternatingRow'}))
    
    for row in rows :
        colsTemp = row.find_all("td")
        cols = list(map(lambda x: x.text , colsTemp))
        # print(cols)
        table.append(cols)

def GetTable():
    global page, payload, payloadTable, cookies
     
    # check Exist Pandas Table
    if os.path.exists("PandaDBCorces.csv"):
        temp = pd.read_csv("PandaDBCorces.csv")
        return temp.drop(columns = [temp.columns[0]])

    # Temp Page List
    lists = requests.post(url+"/list_ara.aspx",data=payload,cookies=cookies)

    # First Page List
    SetPayloadList(lists,1)
    payloadTable['ctl00$ScriptManager1'] = 'ctl00$UpdatePanel1|ctl00$ContentPlaceHolder1$btnSave4'
    payloadTable.__setitem__('ctl00$ContentPlaceHolder1$btnSave4','جــســتجــوی دروس')
    content = requests.post(url+"/list_ara.aspx",cookies=cookies,data=payloadTable)
    payloadTable.__delitem__('ctl00$ContentPlaceHolder1$btnSave4')
    page += 1

    # Parse Page Body
    soup = BeautifulSoup(content.text, 'html.parser')

    # ParsTable
    parsTable(soup)

    # More Page
    while(1):
        try:
            # set Payload and Post Request
            SetPayloadList(content,page)
            content = requests.post(url+"/list_ara.aspx",cookies=cookies,data=payloadTable)
            
            # Parse Page Body
            soup = BeautifulSoup(content.text, 'html.parser')
            
            # ParsTable
            parsTable(soup)

            # Parse Last Page Number
            PageNumber = soup.find_all('tr',{"class": "pgr"})[0].find_all('td')[-1].text
            
            # Check Page Number
            if(PageNumber != "..." and int(PageNumber) == page):
                break
            page += 1
        except:
            pass

    SaveTable(table)
    return SetPandas(table)

def SetPandas(dataTable):
    # Head
    fieldnames = ['CourseId', 'CourseName', 'ClassSection', 'Theoretical', 'PracticalType', 'PracticalTypes',
                    'Gender', 'ClassGroup', 'Rest', 'timeClass', 'ExamTime', 'DateExam', 'ProfessorName', 'Grouping']
    
    # Creat Data Frame
    pdTable = pd.DataFrame({
                    fieldnames[0]: list(int(j[0]) for j in dataTable),
                    fieldnames[1]: list(j[1] for j in dataTable),
                    fieldnames[2]: list(j[2] for j in dataTable),
                    fieldnames[3]: list(j[3] for j in dataTable),
                    fieldnames[4]: list(j[4] for j in dataTable),
                    fieldnames[5]: list(j[5] for j in dataTable),
                    fieldnames[6]: list(j[6] for j in dataTable),
                    fieldnames[7]: list(j[7] for j in dataTable),
                    fieldnames[8]: list(j[8] for j in dataTable), 
                    fieldnames[9]: list(j[9] for j in dataTable), 
                    fieldnames[10]: list(j[10] for j in dataTable),
                    fieldnames[11]: list(j[11] for j in dataTable), 
                    fieldnames[12]: list(j[12] for j in dataTable), 
                    fieldnames[13]: list(j[13] for j in dataTable)
                    })

    # DataFrame To CSV
    pdTable.to_csv("PandaDBCorces.csv", sep=",", encoding='utf-8')

    return pdTable

def GetReportCard():
    global cookies , courseList, courseTable
    requests.get(url+"/Karnameha.aspx",cookies=cookies)
    report = requests.get(url+"/totalkarnameh.aspx",cookies=cookies)

    # ctl00_term , ctl00_ContentPlaceHolder1_dataListTotalkarnameh_ctl???_riz_karnameh_Label1

    soup = BeautifulSoup( report.text , 'html.parser' )

    # Get Date
    date = soup.find_all(id='ctl00_term')[0].text + '   عادی'

    # print(date)

    for i in range(100) :
        dateTow = soup.find(id=str('ctl00_ContentPlaceHolder1_dataListTotalkarnameh_ctl0{}_riz_karnameh_Label1'.format(i)))
        if dateTow.text == date :
            tableRow = dateTow.parent.parent.parent
            rows = tableRow.find_all('tr',{'class':'GridViewRow'})
            rows.extend(tableRow.find_all('tr',{'class':'GridViewAlternatingRow'}))
            # print(rows)
            for row in rows :
                colsTemp = row.find_all("td")
                cols = list(map(lambda x: x.text , colsTemp))
                # print(cols)
                tableCource.append(cols)
            break

    # Get Row Table
    for row in tableCource: courseList.append(courseTable.where(courseTable['CourseId']==int(row[1])).dropna())

    return courseList

def convetToHtmlGrid(dataTable):
    html = pd.concat(dataTable).to_html()
    file = open('CourseList.html','w',encoding='utf-8')
    file.write(html)

# ----------------------Main------------------------
def main():
    global cookies, ReportCard, courseTable, user, pasw
    # print(sys.argv)
    
    if len(sys.argv) != 3:
        print('Please enter the correct parameter >>> Example: python kiauRequest.py UserName PassWord')
        exit()
    # SetUser Information
    user = sys.argv[1]
    pasw = sys.argv[2]
    
    try:
        # Update Session
        GetNewSession()

        # Get All Row DarsHayeErae Shode
        courseTable = GetTable()

        # Get ReportCard
        ReportCard = GetReportCard()

        # Convert data to Grid
        convetToHtmlGrid(ReportCard)
    except:
        print('The username or password is incorrect')

if __name__ == '__main__': main()
