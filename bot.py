#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2
import ssl
import mysql.connector
from bs4 import BeautifulSoup
import re
import datetime
import locale

locale.setlocale(locale.LC_ALL, "tr_TR")

mydb = mysql.connector.connect(
  host="****",
  user="***",
  passwd="***",
  database="****"
)
mycursor = mydb.cursor()

def getJSONData(url):
  context = ssl._create_unverified_context()
  response = urllib2.urlopen(url, context=context)
  data = response.read()
  values = json.loads(data)
  return values

def getCityAndDistrict():
  mycursor.execute("SELECT * FROM country ORDER BY id ASC")
  myresult = mycursor.fetchall()

  for x in myresult:
    url = "https://namazvakitleri.diyanet.gov.tr/tr-TR/home/GetRegList?ChangeType=country&CountryId=" + str(
      x[1]) + "&Culture=tr-TR"
    city = getJSONData(url)

    sqlCity = "INSERT INTO city (countryId, val, name) VALUES "
    for itemc in city['StateList']:
      sqlCity += "(" + str(x[1]) + ", " + itemc['SehirID'] + ", \"" + itemc['SehirAdi'] + "\"), "

      url = "https://namazvakitleri.diyanet.gov.tr/tr-TR/home/GetRegList?ChangeType=state&CountryId=" + str(
        x[1]) + "&Culture=tr-TR&StateId=" + str(itemc['SehirID'])
      district = getJSONData(url)

      sqlDistrict = "INSERT INTO district (countryId, cityId, val, name, url) VALUES "
      for itemd in district['StateRegionList']:
        sqlDistrict += "(" + str(x[1]) + ", " + itemc['SehirID'] + ", " + itemd['IlceID'] + ", \"" + itemd[
          'IlceAdi'] + "\", \"" + itemd['IlceUrl'] + "\"), "

      print(sqlDistrict[:-2])
      mycursor.execute(sqlDistrict[:-2])
      mydb.commit()
      print("cityId: " + str(itemc['SehirID']) + " - insert yapıldı")

    print(sqlCity[:-2])
    mycursor.execute(sqlCity[:-2])
    mydb.commit()
    print("countryId: " + str(x[1]) + " - insert yapıldı")
    print("-------------------")

def vakitBot():
  mycursor.execute("SELECT * FROM district ORDER BY id ASC")
  myresult = mycursor.fetchall()

  for x in myresult:
    print(x)
    pattern = re.compile('<td>(.*?)</td>', re.I | re.S)
    context = ssl._create_unverified_context()
    url = "https://namazvakitleri.diyanet.gov.tr"+str(x[5])
    url_oku = urllib2.urlopen(url, context=context)
    soup = BeautifulSoup(url_oku, 'html.parser')

    table = soup.find("div", {"id": "tab-1"})
    rows = list()
    i = 0
    breakControl = True
    for row in table.findAll("tr"):
      if breakControl:
        if i == 0:
          i = 1
          continue

        line = list()
        k=0
        for each in pattern.findall(str(row)):
          if k == 0:
            k = 1
            dateTime = datetime.datetime.strptime(str(each), "%d %B %Y %A")
            each = dateTime.strftime('%d.%m.%Y')

          #Kalan günler daha sonra çekilecek
          if (each == '20.04.2021'):
            breakControl = False
            break

          line.append(each)

        if line:
          rows.append(line)

    # print(rows)
    sqlVakit = "INSERT INTO vakit (countryId, cityId, districtId, tarih, imsak, gunes, ogle, ikindi, aksam, yatsi) VALUES "
    for item in rows:
      sqlVakit += "(" + str(x[1]) + ", " + str(x[2])+ ", " + str(x[3])+ ", \"" + item[0]+ "\", \"" + item[1]+ "\", \"" + item[2]+ "\", \"" \
                  + item[3]+ "\", \"" + item[4]+ "\", \"" + item[5] + "\", \"" + item[6] + "\"), "

    print(sqlVakit[:-2])
    mycursor.execute(sqlVakit[:-2])
    mydb.commit()
    print("id: "+str(x[0])+" | "+str(x[3])+' - tamamlandı')

if __name__ == '__main__':
  # Ülkeleri manuel insert edip 116. satırı açıp 117. yi kapatıyoruz
  # getCityAndDistrict()

  # Tüm şehir ve ilçe bilgisini aldıktan sonra aşağıdaki satırı uncomment yapıp tüm vakitleri alıyoruz
  vakitBot()