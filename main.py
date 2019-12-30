import xml.etree.cElementTree as ET
import os
import sys
import chardet
import rarfile
import pysftp
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QTableWidgetItem
 
# Импортируем форму.
from proba import Ui_MainWindow
import sys

DAY = [ "Понедельник", "Вторник", "Среда", "Чертверг", "Пятница", "Суббота", "Воскресение" ]
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
        srv = pysftp.Connection(host="193.107.237.33", username="channel4", password="Import1", cnopts=cnopts)
        srv.put("p_p" + (datetime.now()).strftime('%m_%d_%Y') + ".xml", 'app/web/uploads/programa_peredach.xml')
        srv.close()
    except:
        print("Couldn't connect to new.channel4.ru")
        return False
    return True
 
class mywindow(QtWidgets.QMainWindow):
    files = ""
    tree = ET.Element("TVPrograms")
    def __init__(self):
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setAcceptDrops(True)
 
        self.ui.tableWidget.setColumnCount(len(Columns))
        self.ui.tableWidget.setRowCount(1)
 
        self.ui.tableWidget.setHorizontalHeaderLabels(Columns)
    
        self.ui.actionOpen.triggered.connect(self.MenuOpenClicked)
        #self.ui.actionSave.triggered.connect(self.MenuSaveClicked)
        #self.ui.actionSend.triggered.connect(self.MenuSendClicked)
        self.ui.actionExit.triggered.connect(self.MenuExitClicked)
        self.ui.pushButtonExit.clicked.connect(self.MenuExitClicked)

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
   
        return True

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
                    
        print(dat)
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
        

    def load_file(self):
        self.tableclear()
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
              
            mywindow.tree.clear()
            self.create_tree(text, we, dt_rar)
            
            we += 1
            count += 1
            
        print(mywindow.tree.tag)
        self.read_XML()

    def MenuExitClicked(self):
        sys.exit()
        
    def MenuOpenClicked(self):
        for d in DAY:
            self.ui.comboBox.addItem(d)


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
        self.load_file()

    def tableclear(self):
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setHorizontalHeaderLabels(Columns)
            
app = QtWidgets.QApplication([])
application = mywindow()
application.show()
 
sys.exit(app.exec())
