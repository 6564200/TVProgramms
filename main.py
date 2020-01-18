# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import glob, os
import sys
import chardet
import rarfile
import pysftp
import datetime
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidgetItem, QDateTimeEdit, QMessageBox
from PyQt5.QtCore import QDate, QTime, QDateTime
 
from proba import Ui_MainWindow
import sys

color_index = {7: QColor(40,50,180), 1: QColor(80,30,80), 2: QColor(40,100,50), 3: QColor(200,50,50), 4: QColor(40,180,20), 5: QColor(180,30,80), 6: QColor(0,10,10)}

DAY = [ "Понедельник", "Вторник", "Среда", "Чертверг", "Пятница", "Суббота", "Воскресение" ]
AGE = [ "+0", "+6", "+16", "+40" ]
Columns = ('Date', 'Time', 'Name', 'Age')
#TVPrograms = ET.Element("TVPrograms")
rar = " "

def date_time_rar(Rfile): ## дата упаковки файла 
    print(Rfile)
    Yaer = Rfile.getinfo(Rfile.namelist()[1]).date_time[0]
    Month = Rfile.getinfo(Rfile.namelist()[1]).date_time[1]
    Day = Rfile.getinfo(Rfile.namelist()[1]).date_time[2]
    datetime_Rfile = datetime.strptime(str(Day)+"/"+str(Month)+"/"+str(Yaer)+" 10:00:00", '%d/%m/%Y %H:%M:%S')
    print("Date add file in rarfile: " + datetime_Rfile.strftime("%d-%m-%Y"))
    return(datetime_Rfile)
    
def sendSFTP():
    print("Send to site channel4.ru")
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    try:
        srv = pysftp.Connection(host="193.107.237.33", username="***", password="****", cnopts=cnopts)
        srv.put("p_p" + (datetime.now()).strftime('%m_%d_%Y') + ".xml", 'app/web/uploads/programa_peredach.xml')
        srv.close()
        print("Connect to new.channel4.ru")
    except:
        print("Couldn't connect to new.channel4.ru")
        return False
    return True
    

class mywindow(QtWidgets.QMainWindow):
    files = ""
    tree = ET.Element("TVPrograms")
    CURENT = 0
    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setAcceptDrops(True)
        
        self.ui.dateEdit.setDate(QDate.currentDate())
        
        self.ui.tableWidget.setSortingEnabled(True)
        self.ui.tableWidget.setColumnCount(len(Columns))
        #self.ui.tableWidget.setRowCount(1)
 
        self.ui.tableWidget.setHorizontalHeaderLabels(Columns)
    
        self.ui.actionMergeXML.triggered.connect(self.MenuMergeXMLClicked)
        self.ui.actionOpen.triggered.connect(self.MenuOpenClicked)
        self.ui.pushButtonDEL.clicked.connect(self.DELClicked)
        self.ui.pushButtonDate.clicked.connect(self.DateClicked)
        self.ui.pushButtonSend.clicked.connect(self.ButtonSendClicked)
        self.ui.pushButtonSave.clicked.connect(self.MenuSaveClicked)
        self.ui.actionSend.triggered.connect(self.MenuSendClicked)
        self.ui.pushButton_Download.clicked.connect(self.ButtonDownload)
        self.ui.actionExit.triggered.connect(self.MenuExitClicked)
        self.ui.pushButtonExit.clicked.connect(self.MenuExitClicked)
        self.ui.pushButton.clicked.connect(self.InsertProg)
        self.ui.tableWidget.cellClicked[int, int].connect(self.clickedRowColumn)

    def MenuMergeXMLClicked(self):
        print("Объединение XML")
        xml_element_tree = None
        for xml_file in glob.glob("*.xml"):
            data = ET.parse(xml_file).getroot()
            print(xml_file)
            for result in data.iter('TVDay'):
                if xml_element_tree is None:
                    xml_element_tree = data 
                    insertion_point = xml_element_tree.findall("./TVDay")[0]
                else:
                    insertion_point.extend(result)
                    
        for TVDay in xml_element_tree.findall('TVDay'):
            print(TVDay.find('Date').text)
            for tvlist in TVDay.findall('TVList'):
                for tvprogram in tvlist.findall('TVProgram'):
                    #print("/t" + tvprogram.find('Time').text)
                    b = tvprogram.find('ProgramName').text
                    c = tvprogram.find('ProgramAge').text
                    
        root = ET.ElementTree(xml_element_tree)
        root.write("UNION\\merge.xml", encoding="utf-8")


    def UploadSFTP(self):
        print("Upload to site channel4.ru")
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        try:
            srv = pysftp.Connection(host="193.107.237.33", username="channel4", password="Import1", cnopts=cnopts)
            srv.listdir()
            srv.get('app/web/uploads/programa_peredach.xml')
            srv.close()
            print("Connect to new.channel4.ru")

            self.tableclear()
            fxml = mywindow.files = "programa_peredach.xml"
            tree = ET.parse(fxml)
            mywindow.tree = ET.ElementTree(tree)
            self.read_XML()

        except:
            print("Couldn't connect to new.channel4.ru")
            return False
        return True

    def DateClicked(self):
        print(self.ui.dateEdit.date())
        beginDate = self.ui.dateEdit.date().toPyDate()
        print(beginDate)
        itemTime = self.ui.tableWidget.item(0,0).text()
        dt = datetime.strptime(itemTime, '%d-%m-%Y')
        delta = beginDate - dt.date()
        for row in range(self.ui.tableWidget.rowCount()):
            if (self.ui.tableWidget.item(row,0) == None):
              print("ERROR. Пусое поле игнорируем")
            else:
              itemTime = self.ui.tableWidget.item(row,0).text()
              dt = datetime.strptime(itemTime, '%d-%m-%Y')
              self.ui.tableWidget.item(row,0).setText((dt + delta).strftime('%d-%m-%Y'))
        self.setColortoRow()

    def setColortoRow(self):
        for row in range(self.ui.tableWidget.rowCount()):
            if (self.ui.tableWidget.item(row,0) == None):
                A = 0 
            else:
                day = (datetime.strptime(self.ui.tableWidget.item(row,0).text(),'%d-%m-%Y')).isoweekday()
                color = QColor(60+day*20, 200-day*28, 100+day*10)
                self.ui.tableWidget.item(row, 0).setForeground(color_index[day])
                self.ui.tableWidget.item(row, 1).setForeground(color_index[day])
                self.ui.tableWidget.item(row, 2).setForeground(color_index[day])
                self.ui.tableWidget.item(row, 3).setForeground(color_index[day])
        
    
    def clickedRowColumn(self, r, c):
        self.CURENT = r
        
        aaaa = self.ui.tableWidget.item(r,2)
        self.ui.lineEdit.setText(aaaa.text())
        print(aaaa.text())
        self.SetEdit()


    def create_tree(self, txt, we, now):
        week = now.isoweekday() ## день недели даты архива
        tl = txt.splitlines() ## на множество строк
        del tl[0]
        td = timedelta(days=we-week+8) ## понедельник ... вс следующей недели
        d_date = now + td
        
        #print("Create XML element <TVDay><Date> " + d_date.strftime("%d-%m-%Y"))

        TVDay = ET.SubElement(mywindow.tree, "TVDay")
        ET.SubElement(TVDay, "Date").text = d_date.strftime("%d-%m-%Y")
        TVList = ET.SubElement(TVDay, "TVList")

        for line in tl:
          if line != '':
            TVProgram = ET.SubElement(TVList, "TVProgram")
            ET.SubElement(TVProgram, "Time").text = line[:5]
            ET.SubElement(TVProgram, "ProgramName").text = line[6:-4]
            ET.SubElement(TVProgram, "ProgramAge").text = line[-3:]
   
        return d_date

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return super(Window, self).eventFilter(source, event)

    def read_XML(self):
        dat = []       
        root = mywindow.tree  
        for TVDay in root.findall('TVDay'):
            date = TVDay.find('Date').text
            for tvlist in TVDay.findall('TVList'):
                for tvprogram in tvlist.findall('TVProgram'):
                    a = tvprogram.find('Time').text
                    b = tvprogram.find('ProgramName').text
                    c = tvprogram.find('ProgramAge').text
                    dat.append((date, a, b, c))
        row = 0
        for tup in dat:
            col = 0
            for item in tup:
                cellinfo = QTableWidgetItem(item)
                self.ui.tableWidget.setItem(row, col, cellinfo)
                col += 1
            row += 1
            rowPosition = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(rowPosition)
        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.tableWidget.resizeRowsToContents()
        self.setColortoRow()
    
    def load_file_xml(self):
        print("Load XML")
        self.tableclear()
        #mywindow.tree.clear()
        fxml = mywindow.files[8:].replace('/','\\')
        tree = ET.parse(fxml)
        mywindow.tree = ET.ElementTree(tree)
        self.read_XML()
        

    def load_file(self):
        print("Load RAR")
        self.tableclear()
        mywindow.tree.clear()
        frar = mywindow.files[8:].replace('/','\\')
        zf = rarfile.RarFile(frar)
        dt_rar = date_time_rar(zf)
        self.ui.label.setText("Загружен: " + frar + " от " + str(dt_rar)[:-9])

        if len(mywindow.tree.findall('TVDay')) > 0:
            mywindow.tree.clear()
            print(self.ui.tableWidget.rowCount())
            for rPos in range(self.ui.tableWidget.rowCount()):
                print(rPos)
                self.ui.tableWidget.removeRow(1)                                                        


        mywindow.tree.clear()
        count = 0
        we = 0
        for name in zf.namelist():
          if name.find('4K') > -1:
            zf.open(name, 'r')
            txtfile = zf.open(name, 'r')
            
            text = txtfile.read()
            enc = chardet.detect(text).get("encoding")
            
            if enc and enc.lower() != "utf-8":
              text = text.decode(enc)
              
            #
            d_date = self.create_tree(text, we, dt_rar)
            
            we += 1
            count += 1
            
        self.ui.dateEdit.setDate(d_date-timedelta(days=6))    
        print(mywindow.tree.tag)
        self.read_XML()

    def MenuExitClicked(self):
        sys.exit()
        
    def MenuSendClicked(self):
        self.TableToXML()
        sendSFTP()
        
    def DELClicked(self):
        self.ui.tableWidget.removeRow(self.CURENT)
        print(self.CURENT)
    
    def AddLineToTable(self, num_row, dict_row):
        #dict_row = ("10-01-2020", "09.00", "прог", "16+")
        for it in range(len(dict_row)):
            cellinfo = QTableWidgetItem(dict_row[it])
            self.ui.tableWidget.setItem(num_row, it, cellinfo)
        self.setColortoRow()

        
    def InsertProg(self):
        self.ui.tableWidget.insertRow(self.CURENT+1)
        self.AddLineToTable(self.CURENT+1, (self.ui.tableWidget.item(self.CURENT,0).text(), self.ui.tableWidget.item(self.CURENT,1).text(), "прог", "16+"))
        
    def MenuSaveClicked(self):
        print("Save XML")
        self.TableToXML()
        
    def ButtonDownload(self):
        self.UploadSFTP()
        
    def TableToXML(self): ##----------------------------------------------------------------------------------------------------------
      tree = ET.Element("TVPrograms")
      subdate = "00-00-0000"
      for row in range(self.ui.tableWidget.rowCount()):
        if (self.ui.tableWidget.item(row,0) == None):
          print("ERROR. Пусое поле игнорируем")
        else:
          tdate = self.ui.tableWidget.item(row,0).text()
          ttime = self.ui.tableWidget.item(row,1).text()
          tname = self.ui.tableWidget.item(row,2).text()
          tage = self.ui.tableWidget.item(row,3).text()
          #print(tdate, ttime, tname, tage)
          
          if (subdate != tdate):
            TVDay = ET.SubElement(tree, "TVDay")
            ET.SubElement(TVDay, "Date").text = tdate
            subdate = tdate
          
            TVList = ET.SubElement(TVDay, "TVList")

          TVProgram = ET.SubElement(TVList, "TVProgram")
          ET.SubElement(TVProgram, "Time").text = ttime
          ET.SubElement(TVProgram, "ProgramName").text = tname
          ET.SubElement(TVProgram, "ProgramAge").text = tage
        
      root = ET.ElementTree(tree)
      root.write("p_p" + (datetime.now()).strftime('%m_%d_%Y') + ".xml", encoding="utf-8")
      print("Convert Table to XML")
        
        
        
    def ButtonSendClicked(self):
        print("Send to WEB")
        sendSFTP()
        
    def MenuOpenClicked(self):
        print("Open file")
        #self.TableToXML()
        #for d in DAY:
        #    self.ui.comboBox.addItem(d)
            #self.ui.comboBox_2.addItem(self.ui.tableWidget.item(self.CURENT,1).text())
            #self.ui.comboBox_3.addItem(self.ui.tableWidget.item(self.CURENT,3).text())
            
    def SetEdit(self):
        for d in AGE:
            self.ui.comboBox_3.addItem(d)
        text = self.ui.tableWidget.item(self.CURENT,3).text()
        index = self.ui.comboBox_3.findText(text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.ui.comboBox_3.setCurrentIndex(index)
        self.ui.comboBox_2.addItem(self.ui.tableWidget.item(self.CURENT,1).text())


    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        f = e.mimeData().urls()
        mywindow.files = f[0].toString()
        print(mywindow.files)
        if mywindow.files[-3:] == "rar":
            self.load_file()
        else:
            if mywindow.files[-3:] == "xml":
                self.load_file_xml()
            else:
                print("кто это?")

    def tableclear(self):
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setHorizontalHeaderLabels(Columns)
            
app = QtWidgets.QApplication([])
application = mywindow()
application.show()
 
sys.exit(app.exec())
