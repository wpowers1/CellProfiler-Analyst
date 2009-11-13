# -*- Encoding: utf-8 -*-
import os
import re
import wx
import wx.wizard as wiz
from DBConnect import DBConnect
from Properties import Properties
import logging
logging.basicConfig()

db = DBConnect.getInstance()
p = Properties.getInstance()

def makePageTitle(wizPg, title):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(wizPg, -1, title)
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.AddWindow(wx.StaticLine(wizPg, -1), 0, wx.EXPAND|wx.ALL, 5)
        return sizer
     
    
class Page1(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Connect (step 1 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        directions = wx.StaticText(self, -1, "Load a Properties file that contains the database info below.", style=wx.ALIGN_CENTRE)
        browseBtn = wx.Button(self, wx.NewId(), 'Choose file…')
        self.Bind(wx.EVT_BUTTON, self.OnBrowse, browseBtn)
        label_2 = wx.StaticText(self, -1, "DB Host: ")
        self.lblDBHost = wx.StaticText(self, -1, "")
        label_3 = wx.StaticText(self, -1, "DB Name: ")
        self.lblDBName = wx.StaticText(self, -1, "")
        self.btnTest = wx.Button(self, -1, "Test")
        width, height = self.btnTest.GetSize()
        self.btnTest.SetMinSize((200, height))
        self.btnTest.Disable()
        
        label_2.SetMinSize((59, 16))
        self.lblDBHost.SetMinSize((250, 22))
        label_3.SetMinSize((66, 16))
        self.lblDBName.SetMinSize((250, 22))
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridsizer = wx.GridSizer(5, 2, 5, 5)
        sizer1.Add(directions, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(browseBtn, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        gridsizer.Add(label_2, 0, wx.ALIGN_RIGHT, 0)
        gridsizer.Add(self.lblDBHost, 1, 0, 0)
        gridsizer.Add(label_3, 0, wx.ALIGN_RIGHT, 0)
        gridsizer.Add(self.lblDBName, 1, 0, 0)
        sizer1.Add(gridsizer, 0, 0, 0)
        sizer1.Add(self.btnTest, 0, wx.ALIGN_CENTER)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.btnTest.Bind(wx.EVT_BUTTON, self.OnTest)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

    def OnBrowse(self, evt):
        dlg = wx.FileDialog(self, "Select a properties file", defaultDir=os.getcwd(), style=wx.OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            p = Properties.getInstance()
            p.LoadFile(dlg.GetPath())
            self.lblDBHost.SetLabel(p.db_host)
            self.lblDBName.SetLabel(p.db_name)
            self.btnTest.SetLabel('Test')
            self.btnTest.Enable()
        
    def OnTest(self, evt):
        try:
            db.Disconnect()
            db.connect()
            self.btnTest.SetLabel('Connection OK')
            wx.FindWindowById(wx.ID_FORWARD).Enable()
        except:
            self.btnTest.SetLabel('Connection Failed')
        self.btnTest.Disable()
            
    def OnPageChanging(self,evt):
        try:
            if p.db_type.lower()!='mysql':
                raise 'This wizard only supports merging MySQL databases!'
                evt.Veto()
            db.Disconnect()
            db.connect()
            self.btnTest.SetLabel('Connection OK')
            wx.FindWindowById(wx.ID_FORWARD).Enable()
            self.Parent.inDB = self.Parent.outDB = p.db_name
        except:
            self.btnTest.SetLabel('Connection Failed')
            evt.Veto()
        self.btnTest.Disable()
        
        
        
class Page2(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Choose Tables (step 2 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        self.directions = wx.StaticText(self, -1, "Select the tables you wish to include in the master.", style=wx.ALIGN_CENTRE)
        self.listTables = wx.ListBox(self, -1, choices=[], style=wx.LB_HSCROLL|wx.LB_EXTENDED)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.directions, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.listTables, 1, wx.EXPAND, 0)
        
        self.sizer.Add(sizer1, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)
        self.listTables.Bind(wx.EVT_LISTBOX, self.OnSelectItem)
        
    def OnPageLoaded(self, evt):
        self.listTables.Clear()
        perImTables = perObTables = []
        for t in db.GetTableNames():
            # Get tables that are NOT masters (do not have a TableNumber index) 
            indices = [r[4] for r in db.execute('SHOW INDEX FROM %s'%(t))]
            if 'TableNumber' not in indices:
                if t.lower().endswith('per_image'):
                    perImTables += [t]
                if t.lower().endswith('per_object'):
                    perObTables += [t]
        for im in perImTables[::-1]:
            for ob in perObTables:
                if ob[:-10] == im[:-9]:         # if prefixes match, add these two tables
                    prefix = ob[:-10].rstrip('_')
                    self.listTables.Insert(prefix+' ('+im+' / '+ob+')', 0, (im,ob))

    def OnSelectItem(self,evt):
        self.Parent.perImageTables = [self.listTables.GetClientData(i)[0] for i in self.listTables.GetSelections()]
        self.Parent.perObjectTables = [self.listTables.GetClientData(i)[1] for i in self.listTables.GetSelections()]
        self.directions.SetForegroundColour('#000001')
            
    def OnPageChanging(self,evt):
        if self.listTables.GetSelections() == () and evt.GetDirection() == True:
            evt.Veto()
            self.directions.SetForegroundColour('#FF0000')
            


def find_master_tables():
    tables = db.GetTableNames()
    masters = {}
    for t in tables:
        res = db.execute('SHOW INDEX FROM %s'%(t))
        if t.lower().endswith('per_image'):
            if 'TableNumber' in [r[4] for r in res]:
                if not masters.has_key(t[:-10]):
                    masters[t[:-10]] = t
                else:
                    masters[t[:-10]] = t + ',' + masters[t[:-10]] 
        if t.lower().endswith('per_object'):
            if 'TableNumber' in [r[4] for r in res]:
                if not masters.has_key(t[:-11]):
                    masters[t[:-11]] = t
                else:
                    masters[t[:-11]] += ',' + t
    return masters.values()

        
class Page3(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Choose Prefix (step 3 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        self.txtPrefix = wx.TextCtrl(self, -1, 'CPA')
        self.example = wx.StaticText(self, -1, 'Output tables: "CPA_Per_Image", "CPA_Per_Object"')
        self.listTables = wx.ListBox(self, -1, choices=[], style=wx.LB_HSCROLL)
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(wx.StaticText(self, -1, 'Enter a prefix name for your CPA master tables:', style=wx.ALIGN_CENTRE), 0, wx.ALL|wx.EXPAND, 5)
        sizer1.Add(self.txtPrefix, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.example, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        sizer1.Add(wx.StaticText(self, -1, '- OR -', style=wx.ALIGN_CENTER), 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(wx.StaticText(self, -1, 'Select a master to append to:', style=wx.ALIGN_CENTER), 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.listTables, 1, wx.EXPAND, 0)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.txtPrefix.Bind(wx.EVT_TEXT, self.OnText)
        self.listTables.Bind(wx.EVT_LEFT_DOWN, self.OnClickTableList)
        self.txtPrefix.Bind(wx.EVT_LEFT_DOWN, self.OnClickPrefix)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnPageChanging)

    def OnClickTableList(self, evt):
        self.txtPrefix.SetValue('')
        evt.Skip()

    def OnClickPrefix(self, evt):
        self.listTables.DeselectAll()
        evt.Skip()

    def OnPageLoaded(self, evt):
        self.listTables.SetItems(find_master_tables())
        self.OnText(None)
        
    def OnText(self, evt):
        nameRules = re.compile('[a-zA-Z0-9]\w*$')
        if nameRules.match(self.txtPrefix.GetValue()):
            perImage  = self.txtPrefix.GetValue()+'_Per_Image'
            perObject = self.txtPrefix.GetValue()+'_Per_Object'
            if not hasattr(self, 'existingTables'):
                self.existingTables = db.GetTableNames()
            if (perImage not in self.existingTables and 
                perObject not in self.existingTables):
                self.Parent.outPerImage = perImage
                self.Parent.outPerObject = perObject
                self.Parent.masterExists = False
                self.example.SetLabel('Output tables: '+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.txtPrefix.GetValue()+'_table_index')
            else:
                self.example.SetLabel('Table already exists.')
        else:
            self.example.SetLabel('Invalid table prefix.')
            
    def OnPageChanging(self,evt):
        if evt.GetDirection() == True:
            if (self.example.GetLabel() == 'Invalid table prefix.' and 
                self.listTables.GetSelection() == wx.NOT_FOUND):
                evt.Veto()  
            elif self.listTables.GetSelection() != wx.NOT_FOUND:
                self.Parent.outPerImage, self.Parent.outPerObject = self.listTables.GetStringSelection().split(',')
                self.Parent.masterExists = True
            
class Page4(wiz.WizardPageSimple):
    def __init__(self, parent):
        wiz.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, -1, 'Summary (step 4 of 4)')
        title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.sizer.AddWindow(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.sizer.AddWindow(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        
        label_1 = wx.StaticText(self, -1, 'Confirm that the following information is correct and click "Finish".', style=wx.ALIGN_CENTRE)
        self.outDB = wx.StaticText(self, -1, 'Database to write to: ')
        self.inTables = wx.StaticText(self, -1, 'Tables to merge: ')
        self.outTables = wx.StaticText(self, -1, 'Tables to write: ')
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.SetMinSize((600,200))
        sizer1.Add(label_1, 0, wx.ALL|wx.EXPAND, 20)
        sizer1.Add(self.outDB, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.inTables, 0, wx.ALL|wx.EXPAND, 10)
        sizer1.Add(self.outTables, 0, wx.ALL|wx.EXPAND, 10)
        
        self.sizer.Add(sizer1)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnPageLoaded)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnFinish)

    def OnPageLoaded(self, evt):
        import string
        self.outDB.SetLabel('Database to write to: '+self.Parent.outDB)
        self.inTables.SetLabel('Tables to merge: \n'+string.join([str(t[0])+', '+str(t[1]) for t in zip(self.Parent.perImageTables,self.Parent.perObjectTables)],'\n'))
        if self.Parent.masterExists:
            self.outTables.SetLabel('Merging into tables: \n'+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.Parent.outPerImage[:-10]+'_table_index')
        else:
            self.outTables.SetLabel('Tables to write: \n'+self.Parent.outPerImage+', '+self.Parent.outPerObject+', '+self.Parent.outPerImage[:-10]+'_table_index')
        
    def OnFinish(self, evt):
        '''
        DO THE ACTUAL MERGE!
        '''
        
        # TODO: Allow abort from dialog        
        
        if evt.GetDirection() == True:
            nTables = len(self.Parent.perImageTables)
            prefix = self.Parent.outPerImage[:-10]
            dlg = wx.ProgressDialog("Creating Master Tables", "0%", 100, style=wx.PD_CAN_ABORT|wx.PD_SMOOTH)
            dlg.SetSize((400,150))
            dlg.Show()
            
            if self.Parent.masterExists:
                t0 = int(db.execute('SELECT MAX(TableNumber) FROM %s'%(self.Parent.outPerObject))[0][0]) + 1
            else:
                t0 = 0
                    
            # Create the DB if it doesn't exist already
#            db.execute('CREATE DATABASE IF NOT EXISTS '+self.Parent.outDB)
#            db.execute('USE '+self.Parent.outDB)
            
            # Create a table_index table which will be used to link the "TableNumber" fields to the original table names
            db.execute('CREATE TABLE IF NOT EXISTS '+prefix+'_table_index (TableNumber INT, PerImageTable varchar(60), PerObjectTable varchar(60), PRIMARY KEY (TableNumber))')
            for i in xrange(nTables):
                db.execute('INSERT INTO '+prefix+'_table_index (TableNumber, PerImageTable, PerObjectTable) VALUES('+str(t0+i)+', "'+self.Parent.perImageTables[i]+'", "'+self.Parent.perObjectTables[i]+'")')
            
            # Create the per_image tables
            if not self.Parent.masterExists:
                db.execute('CREATE TABLE IF NOT EXISTS '+self.Parent.outPerImage+' LIKE '+self.Parent.inDB+'.'+self.Parent.perImageTables[0])
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' DROP PRIMARY KEY')
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' ADD COLUMN TableNumber INT')
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' ADD PRIMARY KEY (TableNumber, ImageNumber)')
            else:
                lastcol = db.GetColumnNames(self.Parent.outPerImage)[-1]
                db.execute('ALTER TABLE '+self.Parent.outPerImage+' MODIFY COLUMN TableNumber INT AFTER '+lastcol)
            
            dlg.Update(0, 'Creating "'+self.Parent.outPerImage+'": 0%')
            for i in xrange(nTables):
                db.execute('INSERT INTO '+self.Parent.outPerImage+' SELECT *,'+str(t0+i)+' FROM '+self.Parent.inDB+'.'+self.Parent.perImageTables[i])
                percent = 100*i/nTables
                dlg.Update(percent, '"Creating "'+self.Parent.outPerImage+'": '+str(percent)+'%')
            db.execute('ALTER TABLE '+self.Parent.outPerImage+' MODIFY COLUMN TableNumber INT FIRST')
            
            # Create the per_object tables
            if not self.Parent.masterExists:
                db.execute('CREATE TABLE IF NOT EXISTS '+self.Parent.outPerObject+' LIKE '+self.Parent.inDB+'.'+self.Parent.perObjectTables[0])
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' DROP PRIMARY KEY')
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' ADD COLUMN TableNumber INT')
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' ADD PRIMARY KEY (TableNumber, ImageNumber, ObjectNumber)')
            else:
                lastcol = db.GetColumnNames(self.Parent.outPerObject)[-1]
                db.execute('ALTER TABLE '+self.Parent.outPerObject+' MODIFY COLUMN TableNumber INT AFTER '+lastcol)
            
            dlg.Update(0, 'Creating "'+self.Parent.outPerObject+'": 0%')
            for i in xrange(nTables):
                db.execute('INSERT INTO '+self.Parent.outPerObject+' SELECT *,'+str(t0+i)+' FROM '+self.Parent.inDB+'.'+self.Parent.perObjectTables[i])
                percent = 100*i/nTables
                dlg.Update(percent, 'Creating table "'+self.Parent.outPerObject+'": '+str(percent)+'%')
            db.execute('ALTER TABLE '+self.Parent.outPerObject+' MODIFY COLUMN TableNumber INT FIRST')
            
            # Log the newly created table names in CPA_Merged_Tables.merged
            db.execute('INSERT INTO CPA_Merged_Tables.merged (per_image, per_object, table_index) VALUES("'+self.Parent.outDB+'.'+self.Parent.outPerImage+'", "'+self.Parent.outDB+'.'+self.Parent.outPerObject+'", "'+self.Parent.outDB+'.'+prefix+'_table_index")' )
            
            dlg.Destroy()
            
            


app = wx.PySimpleApp()
wizard = wiz.Wizard(None, -1, "Create Master Table")
page1 = Page1(wizard)
page2 = Page2(wizard)
page3 = Page3(wizard)
page4 = Page4(wizard)
wiz.WizardPageSimple_Chain(page1,page2)
wiz.WizardPageSimple_Chain(page2,page3)
wiz.WizardPageSimple_Chain(page3,page4)
wizard.FitToPage(page1)
wizard.RunWizard(page1)
wizard.Destroy()
app.MainLoop()
