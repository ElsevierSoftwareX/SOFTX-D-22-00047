# Cloud2FEM - FE mesh generator based on point clouds of existing/historical structures
# Copyright (C) 2022  Giovanni Castellazzi, Nicolò Lo Presti, Antonio Maria D'Altri, Stefano de Miranda
#
# This file is part of Cloud2FEM.
#
# Cloud2FEM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Cloud2FEM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.





import shelve
import numpy as np
from pyntcloud import PyntCloud
import shapely.geometry as sg
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDialog
from PyQt5.uic import loadUi
import pyqtgraph as pg
from pyqtgraph import PlotWidget

from Vispy3DViewer import Visp3dplot
import Cloud2Polygons as cp
import Polygons2FEM as pf
import plot2D as ptd


class MainContainer:
    def __init__(self, filepath=None, pcl=None, npts=None, zmin=None, zmax=None,
                 xmin=None, xmax=None, ymin=None, ymax=None, zcoords=None,
                 slices=None, netpcl=None, ctrds=None, polys=None, cleanpolys=None,
                 polygs=None, xngrid=None, xelgrid=None, yngrid=None, yelgrid=None,
                 elemlist=None, nodelist=None, elconnect=None, temp_points=None,
                 temp_scatter=None, temp_polylines=None, temp_roi_plot=None,
                 editmode=None, roiIndex=None):
        self.filepath = filepath
        self.pcl = pcl              # Whole PCl as a 3-columns xyz numpy array
        self.npts = npts            # the above 'pcl' number of points
        self.zmin = zmin
        self.zmax = zmax
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.zcoords = zcoords      # 1D Numpy array of z coordinates utilized to create the slices below
        self.slices = slices        # Dictionary where key(i)=zcoords(i) and value(i)=np_array_xy(i)
        self.netpcl = netpcl        # pcl with empty spaces at slices position (for 3D visualization purposes)
        self.ctrds = ctrds          # Dictionary ordered as done for dict "slices"
        self.polys = polys          # Dict key(i) = zcoords(i), value(i) = [[np.arr.poly1],[np.a.poly2],[..],[np.polyn]]
        self.cleanpolys = cleanpolys  # Polylines cleaned by the shapely simplify function
        self.polygs = polygs        # Dict key(i) = zcoords(i), value(i) = shapely MultiPolygon
        self.xngrid = xngrid
        self.xelgrid = xelgrid
        self.yngrid = yngrid
        self.yelgrid = yelgrid
        self.elemlist = elemlist    # Dict key(i) = zcoords(i), value(i) = [[x1, y1], [x2, y2], ..., [xn, yn]]
        self.nodelist = nodelist    # Np array, row[i] = [nodeID, x, y, z]
        self.elconnect = elconnect  # Np array, row[i] = [edelmID, nID1, nID2, nID3, nID4, nID5, nID6, nID7, nID8]




mct = MainContainer()  # All the main variables are stored here


def save_project():
    try:
        fd = QFileDialog()
        filepath = fd.getSaveFileName(parent=None, caption="Save Project", directory="",
                                      filter="Cloud2FEM Data (*.cloud2fem)")[0]
        s = shelve.open(filepath)
        mct_dict = mct.__dict__  # Special method: convert instance of a class to a dict
        for k in mct_dict.keys():
            if k in ['filepath', 'pcl', 'netpcl', 'editmode', 'roiIndex', 
                     'temp_roi_plot', 'temp_polylines', 'temp_scatter', 'temp_points']:
                continue
            else:
                s[k] = mct_dict[k]
        s.close()
    except (ValueError, TypeError, FileNotFoundError):
        print('No file name specified')

def open_project():
        try:
            fd = QFileDialog()
            filepath = fd.getOpenFileName(parent=None, caption="Open Project", directory="",
                                         filter="Cloud2FEM Data (*.cloud2fem.dat)")[0]
            s = shelve.open(filepath[: -4])

            mct.npts = s['npts']
            mct.zmin = s['zmin']
            mct.zmax = s['zmax']
            mct.xmin = s['xmin']
            mct.xmax = s['xmax']
            mct.ymin = s['ymin']
            mct.ymax = s['ymax']
            try:
                mct.zcoords = s['zcoords']
            except KeyError:
                mct.zcoords = s['zslices']
            mct.slices = s['slices']
            mct.ctrds = s['ctrds']
            mct.polys = s['polys']
            mct.cleanpolys = s['cleanpolys']
            mct.polygs = s['polygs']
            mct.xngrid = s['xngrid']
            mct.xelgrid = s['xelgrid']
            mct.yngrid = s['yngrid']
            mct.yelgrid = s['yelgrid']
            mct.elemlist = s['elemlist']
            mct.nodelist = s['nodelist']
            mct.elconnect = s['elconnect']
            s.close()

            for z in mct.zcoords:
                win.combo_slices.addItem(str('%.3f' % z))
            win.main2dplot()

            win.label_zmin_value.setText(str(mct.zmin))
            win.label_zmax_value.setText(str(mct.zmax))
            win.btn_3dview.setEnabled(True)
            win.check_pcl_slices.setEnabled(True)
            win.status_slices.setStyleSheet("background-color: rgb(0, 255, 0);")
            win.btn_gen_centr.setEnabled(True)
            win.lineEdit_wall_thick.setEnabled(True)
            win.lineEdit_xeldim.setEnabled(True)
            win.lineEdit_yeldim.setEnabled(True)
            win.check_pcl.setChecked(False)
            win.check_pcl.setEnabled(False)
            win.btn_edit.setEnabled(True)

            if mct.ctrds != None:
                win.check_centroids.setEnabled(True)
                win.status_centroids.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_polylines.setEnabled(True)
                win.radioCentroids.setEnabled(True)
            if mct.cleanpolys != None:
                win.check_polylines.setEnabled(True)
                win.status_polylines.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_polygons.setEnabled(True)
                win.radioPolylines.setEnabled(True)
                win.btn_copy_plines.setEnabled(True)
            if mct.polygs != None:
                win.status_polygons.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.btn_gen_mesh.setEnabled(True)
                win.exp_dxf.setEnabled(True)
            if mct.elemlist != None:
                win.status_mesh.setStyleSheet("background-color: rgb(0, 255, 0);")
                win.exp_mesh.setEnabled(True)

        except ValueError:
            print('No project file selected')



def loadpcl():
    """ Opens a FileDialog to choose the PCl and stores the
    values for filepath, pcl, npts, zmin and zmax. Then sets up the gui.
    """
    try:
        fd = QFileDialog()
        getfile = fd.getOpenFileName(parent=None, caption="Load Point Cloud", directory="",
                                     filter="Point Cloud Data (*.pcd);; Polygon File Format (*.ply)")
        mct.filepath = getfile[0]
        wholepcl = PyntCloud.from_file(mct.filepath)
        mct.npts = wholepcl.points.shape[0]          # Point Cloud number of points

        # Defines a 3-columns xyz numpy array
        mct.pcl = np.hstack((
            np.array(wholepcl.points['x']).reshape(mct.npts, 1),
            np.array(wholepcl.points['y']).reshape(mct.npts, 1),
            np.array(wholepcl.points['z']).reshape(mct.npts, 1)
        ))
        mct.zmin = mct.pcl[:, 2].min()
        win.label_zmin_value.setText(str(mct.zmin))
        mct.zmax = mct.pcl[:, 2].max()
        win.label_zmax_value.setText(str(mct.zmax))
        mct.xmin = mct.pcl[:, 0].min()
        mct.xmax = mct.pcl[:, 0].max()
        mct.ymin = mct.pcl[:, 1].min()
        mct.ymax = mct.pcl[:, 1].max()
        print("\nPoint Cloud of " + str(mct.pcl.shape[0]) + " points loaded, file path: " + mct.filepath)
        print("First three points:\n" + str(mct.pcl[:3]))
        print("Last three points:\n" + str(mct.pcl[-3:]))
        if len(mct.filepath) < 65:
            win.loaded_file.setText("Loaded Point Cloud: " + mct.filepath + "   ")
        else:
            slashfound = 0
            head_reverse = ''
            for char in mct.filepath[:30][::-1]:
                if char == '/' and slashfound == 0:
                    slashfound += 1
                elif slashfound == 0:
                    continue
                else:
                    head_reverse += char
            path_head = head_reverse[::-1]

            slashfound = 0
            path_tail = ''
            for char in mct.filepath[30:]:
                if char == '/' and slashfound == 0:
                    slashfound += 1
                elif slashfound == 0:
                    continue
                else:
                    path_tail += char
            win.loaded_file.setText("Loaded Point Cloud: " + path_head + '/...../' + path_tail + "   ")
            win.status_slices.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")

        # Enable gui widgets
        win.btn_3dview.setEnabled(True)
        win.rbtn_fixnum.setEnabled(True)
        win.rbtn_fixstep.setEnabled(True)
        win.lineEdit_from.setEnabled(True)
        win.lineEdit_to.setEnabled(True)
        win.lineEdit_steporN.setEnabled(True)
        win.lineEdit_thick.setEnabled(True)
        win.btn_gen_slices.setEnabled(True)
    except ValueError:
        print('No Point Cloud selected')



class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("gui_main.ui", self)
        self.setWindowTitle('Cloud2FEM')
        self.graphlayout.setBackground((255, 255, 255))
        self.plot2d = self.graphlayout.addPlot()
        self.plot2d.setAspectLocked(lock=True)
        self.plot2d.setTitle('')

        self.Load_PC.triggered.connect(loadpcl)
        self.save_project.triggered.connect(save_project)
        self.open_project.triggered.connect(open_project)
        self.exp_dxf.triggered.connect(self.exp_dxf_clicked)
        self.exp_mesh.triggered.connect(self.exp_mesh_clicked)
        self.btn_3dview.clicked.connect(self.open3dview)

        self.rbtn_fixnum.toggled.connect(self.fixnum_toggled)
        self.rbtn_fixstep.toggled.connect(self.fixstep_toggled)

        self.btn_gen_slices.clicked.connect(self.genslices_clicked)
        self.btn_gen_centr.clicked.connect(self.gencentr_clicked)
        self.btn_gen_polylines.clicked.connect(self.genpolylines_clicked)
        self.btn_gen_polygons.clicked.connect(self.genpolygons_clicked)
        self.btn_gen_mesh.clicked.connect(self.genmesh_clicked)
        self.combo_slices.currentIndexChanged.connect(self.main2dplot)
        self.check_2d_slice.toggled.connect(self.main2dplot)
        self.check_2d_grid.toggled.connect(self.main2dplot)
        self.check_2d_centr.toggled.connect(self.main2dplot)
        self.check_2d_polylines.toggled.connect(self.main2dplot)
        self.check_2d_polylines_clean.toggled.connect(self.main2dplot)
        self.lineEdit_xeldim.editingFinished.connect(self.main2dplot)
        self.lineEdit_yeldim.editingFinished.connect(self.main2dplot)
        # Connect edit signals
        self.btn_edit.clicked.connect(self.editMode)
        self.lineEdit_off.textEdited.connect(self.updateOffDistance)
        self.btn_edit_discard.clicked.connect(self.discard_changes)
        self.btn_edit_finalize.clicked.connect(self.save_changes)
        self.btn_copy_plines.clicked.connect(self.copy_polylines)
        
        # Set some default values
        self.emode = None  # Edit mode status
        self.staticPlotItems = []  # List of non editable plotted items



    def genslices_clicked(self):
        self.plot2d.vb.enableAutoRange()
        a = self.lineEdit_from.text()
        b = self.lineEdit_to.text()
        c = self.lineEdit_steporN.text()
        d = self.lineEdit_thick.text()
        try:
            if len(a) == 0 or len(b) == 0 or len(c) == 0 or len(d) == 0:
                msg_slices = QMessageBox()
                msg_slices.setWindowTitle('Slicing configuration')
                msg_slices.setText('\nIncomplete slicing configuration            '
                                   '\n                                            ')
                msg_slices.setIcon(QMessageBox.Warning)
                x = msg_slices.exec_()
            else:
                if self.rbtn_fixnum.isChecked():
                    mct.zcoords = cp.make_zcoords(a, b, c, 1)
                elif self.rbtn_fixstep.isChecked():
                    mct.zcoords = cp.make_zcoords(a, b, c, 2)
                else:
                    pass
                    
                mct.slices, mct.netpcl = cp.make_slices(mct.zcoords, mct.pcl, float(d), mct.npts)
                self.combo_slices.clear()
                for z in mct.zcoords:
                    self.combo_slices.addItem(str('%.3f' % z))  # Populates the gui slices combobox
                
                print(len(mct.slices.keys()), ' slices generated')
                self.lineEdit_wall_thick.setEnabled(True)
                self.btn_gen_centr.setEnabled(True)
                self.btn_edit.setEnabled(True)
                self.check_pcl_slices.setEnabled(True)
                self.lineEdit_xeldim.setEnabled(True)
                self.lineEdit_yeldim.setEnabled(True)
                self.status_slices.setStyleSheet("background-color: rgb(0, 255, 0);")
                self.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
                self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
                msg_slicesok = QMessageBox()
                msg_slicesok.setWindowTitle('Slicing completed')
                msg_slicesok.setText(str(len(mct.slices.keys())) + ' slices generated    '
                                                                   '                     ')
                x = msg_slicesok.exec_()
        except ValueError:
            msg_slices2 = QMessageBox()
            msg_slices2.setWindowTitle('Slicing configuration')
            msg_slices2.setText('ValueError')
            msg_slices2.setInformativeText("Only the following input types are allowed:\n\n"
                                           "From:\n"
                                           "        integer or float\n"
                                           "to:\n"
                                           "        integer or float\n"
                                           "n° of slices:\n"
                                           "        integer\n"
                                           "step height:\n"
                                           "        integer or float")
            msg_slices2.setIcon(QMessageBox.Warning)
            x = msg_slices2.exec_()

    def gencentr_clicked(self):
        self.plot2d.vb.enableAutoRange()
        try:
            minwthick = float(self.lineEdit_wall_thick.text())
            
            mct.ctrds = cp.find_centroids(minwthick, mct.zcoords, mct.slices)
            
            self.check_centroids.setEnabled(True)
            self.radioCentroids.setEnabled(True)
            self.btn_gen_polylines.setEnabled(True)
            self.status_centroids.setStyleSheet("background-color: rgb(0, 255, 0);")
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.main2dplot()
            msg_centrok = QMessageBox()
            msg_centrok.setWindowTitle('Generate Centroids')
            msg_centrok.setText('\nCentroids generation completed           '
                                '\n                                         ')
            x = msg_centrok.exec_()
        except ValueError:
            msg_centr = QMessageBox()
            msg_centr.setWindowTitle('Generate Centroids')
            msg_centr.setText('\nWrong input in "Minimum wall thickness"       '
                               '\n                                            ')
            msg_centr.setIcon(QMessageBox.Warning)
            x = msg_centr.exec_()

    def genpolylines_clicked(self):
        self.plot2d.vb.enableAutoRange()
        minwthick = float(self.lineEdit_wall_thick.text())
        
        mct.polys, mct.cleanpolys = cp.make_polylines(minwthick, mct.zcoords, mct.ctrds)
        
        self.check_polylines.setEnabled(True)
        self.btn_gen_polygons.setEnabled(True)
        self.radioPolylines.setEnabled(True)
        self.btn_copy_plines.setEnabled(True)
        self.status_polylines.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.main2dplot()
        msg_polysok = QMessageBox()
        msg_polysok.setWindowTitle('Generate Polylines')
        msg_polysok.setText('\nPolylines generation completed           '
                            '\n                                         ')
        x = msg_polysok.exec_()

    def genpolygons_clicked(self):
        self.plot2d.vb.enableAutoRange()
        minwthick = float(self.lineEdit_wall_thick.text())
        
        mct.polygs, invalidpolygons = cp.make_polygons(minwthick, mct.zcoords, mct.cleanpolys)
        
        if len(invalidpolygons) != 0:
            msg_invpoligons = QMessageBox()
            msg_invpoligons.setWindowTitle('Generate Polygons')
            invalidlist = ''
            for z in invalidpolygons:
                invalidlist += str('\n' + "%.3f" % z)
            msg_invpoligons.setText("\nInvalid Polygons in slices: " + invalidlist)
            msg_invpoligons.setIcon(QMessageBox.Warning)
            x = msg_invpoligons.exec_()
        
        self.btn_gen_mesh.setEnabled(True)
        self.exp_dxf.setEnabled(True)
        self.status_polygons.setStyleSheet("background-color: rgb(0, 255, 0);")
        self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
        self.main2dplot()
        msg_polygsok = QMessageBox()
        msg_polygsok.setWindowTitle('Generate Polygons')
        msg_polygsok.setText('\nPolygons generation completed           '
                            '\n                                         ')
        x = msg_polygsok.exec_()
        
    def exp_dxf_clicked(self):
        try:
            fd = QFileDialog()
            filepath = fd.getSaveFileName(parent=None, caption="Export DXF", directory="", filter="DXF (*.dxf)")[0]
            cp.export_dxf(mct.zcoords, mct.polygs, filepath)
            msg_dxfok = QMessageBox()
            msg_dxfok.setWindowTitle('DXF Export')
            msg_dxfok.setText('File saved in: \n' + filepath + '                       ')
            x = msg_dxfok.exec_()
        except (ValueError, TypeError, FileNotFoundError):
            print('No dxf name specified')
        
    def genmesh_clicked(self):
        xeldim = float(self.lineEdit_xeldim.text())
        yeldim = float(self.lineEdit_yeldim.text())

        mct.elemlist, mct.nodelist, mct.elconnect = pf.make_mesh(
            xeldim, yeldim, mct.xmin, mct.ymin, mct.xmax, mct.ymax, mct.zcoords, mct.polygs)
        
        self.main2dplot()
        self.exp_mesh.setEnabled(True)
        self.status_mesh.setStyleSheet("background-color: rgb(0, 255, 0);")
        msg_meshok = QMessageBox()
        msg_meshok.setWindowTitle('Generate Mesh')
        msg_meshok.setText('\nMesh generation completed                 '
                            '\n                                         ')
        x = msg_meshok.exec_()
    
    def exp_mesh_clicked(self):
        try:
            fd = QFileDialog()
            meshpath = fd.getSaveFileName(parent=None, caption="Export DXF", directory="", filter="Abaqus Input File (*.inp)")[0]
            pf.export_mesh(meshpath, mct.nodelist, mct.elconnect)
            msg_dxfok = QMessageBox()
            msg_dxfok.setWindowTitle('Mesh Export')
            msg_dxfok.setText('File saved in: \n' + meshpath + '                       ')
            x = msg_dxfok.exec_()
        except (ValueError, TypeError, FileNotFoundError):
            print('No .inp name specified')

    def srule_status(self, torf):
        self.lineEdit_from.setEnabled(torf)
        self.lineEdit_to.setEnabled(torf)
        self.lineEdit_steporN.setEnabled(torf)

    def fixnum_toggled(self):
        self.srule_status(True)
        self.label_steporN.setText('n° of slices:')

    def fixstep_toggled(self):
        self.srule_status(True)
        self.label_steporN.setText('step height:')

    def open3dview(self):
        chkpcl = self.check_pcl.isChecked()
        chksli = self.check_pcl_slices.isChecked()
        chkctr = self.check_centroids.isChecked()
        chkply = self.check_polylines.isChecked()
        if self.rbtn_100.isChecked():
            p3d = Visp3dplot(1)
        elif self.rbtn_50.isChecked():
            p3d = Visp3dplot(0.5)
        else:
            p3d = Visp3dplot(0.1)
        if chkctr:
            p3d.print_centr(mct)
        if chksli:
            p3d.print_slices(mct)
        if chkply:
            p3d.print_polylines(mct)
        if chkpcl and (chksli or chkctr or chkply):
            p3d.print_cloud(mct.netpcl, 0.5)   ############################################ default alpha = 0.75
        elif chkpcl:
            p3d.print_cloud(mct.pcl, 1)
        p3d.final3dsetup()
    
    def plot_grid(self):
        xeldim = float(self.lineEdit_xeldim.text())
        yeldim = float(self.lineEdit_yeldim.text())
        xngrid = np.arange(mct.xmin - xeldim, mct.xmax + 2 * xeldim, xeldim)
        yngrid = np.arange(mct.ymin - yeldim, mct.ymax + 2 * yeldim, yeldim)
        for x in xngrid:
            xitem = pg.PlotCurveItem(pen=pg.mkPen(color=(220, 220, 220, 255), width=1.5))
            xitem.setData(np.array([x, x]), np.array([min(yngrid), max(yngrid)]))
            self.plot2d.addItem(xitem)
            self.staticPlotItems.append(xitem)
        for y in yngrid:
            yitem = pg.PlotCurveItem(pen=pg.mkPen(color=(220, 220, 220, 255), width=1.5))
            yitem.setData(np.array([min(xngrid), max(xngrid)]), np.array([y, y]))
            self.plot2d.addItem(yitem)
            self.staticPlotItems.append(yitem)

    def plot_slice(self):
        slm2dplt = mct.slices[mct.zcoords[self.combo_slices.currentIndex()]][:, [0, 1]]
        scatter2d = pg.ScatterPlotItem(pos=slm2dplt, size=5, brush=pg.mkBrush(0, 0, 0, 255))    #### default size = 5
        self.plot2d.addItem(scatter2d)
        self.staticPlotItems.append(scatter2d)

    def plot_centroids(self):
        ctrsm2dplt = mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]][:, [0, 1]]
        ctrsscatter2d = pg.ScatterPlotItem(pos=ctrsm2dplt, size=9, brush=pg.mkBrush(255, 0, 0, 255)) ######### default size = 13
        self.plot2d.addItem(ctrsscatter2d)
        self.staticPlotItems.append(ctrsscatter2d)

    def plot_polylines(self):
        for poly in mct.polys[mct.zcoords[self.combo_slices.currentIndex()]]:
            item = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 0, 255, 255), width=3))
            item.setData(poly[:, 0], poly[:, 1])
            self.plot2d.addItem(item)
            self.staticPlotItems.append(item)
    
    def plot_polys_clean(self):
        for poly in mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]]:
            item = pg.PlotCurveItem(pen=pg.mkPen(color=(0, 0, 0, 255), width=5))
            item.setData(poly[:, 0], poly[:, 1])
            self.plot2d.addItem(item)
            self.staticPlotItems.append(item)
            pts = pg.ScatterPlotItem(pos=poly[:, : 2], size=9, brush=pg.mkBrush(255, 0, 0, 255), symbol='s')
            self.plot2d.addItem(pts)
            self.staticPlotItems.append(pts)
            

    def main2dplot(self):
        chk2dsli = self.check_2d_slice.isChecked()
        chk2centr = self.check_2d_centr.isChecked()
        chk2dplines = self.check_2d_polylines.isChecked()
        chk2dplclean = self.check_2d_polylines_clean.isChecked()
        chk2dgrid = self.check_2d_grid.isChecked()
        # self.plot2d.clear()
        for item in self.staticPlotItems:
            self.plot2d.removeItem(item)
        self.staticPlotItems = []
        try:
            try:
                if chk2dgrid:
                    self.plot_grid()
            except:
                pass
            if chk2dplines and mct.polys is not None:
                self.plot_polylines()
            if chk2dplclean and mct.cleanpolys is not None:
                self.plot_polys_clean()
            if chk2dsli and mct.slices is not None:
                self.plot_slice()
            if chk2centr and mct.ctrds is not None:
                self.plot_centroids()
            # if mct.temp_scatter is not None:
            #     self.plot2d.addItem(mct.temp_scatter)
        except KeyError:
            print('Error in func main2dplot')
            # pass  # KeyError is raised when re-slicing. It shouldn't cause any problem

    
    def updateOffDistance(self):
        """ This method is needed to update the offset distance when
        a new value is set in the lineEdit widget.
        """
        try:
            self.editInstance[0].offset = float(self.lineEdit_off.text())
        except ValueError:
            pass
    
    def keyPressEvent(self, event):
        ''' This method already exists in the inherited QMainWindow class.
            Here it is overwritten to adapt key events to this app.
        '''
        if self.emode is not None:
            self.lineEdit_off.setEnabled(False)
            self.plot2d.clear()
            self.main2dplot()
            if self.emode == 'polylines':
                self.tempPolylines = []
                for edI in self.editInstance:
                    edI.stop()
                    if self.polylinesTool in ['addponline', 'movepoint']:
                        self.tempPolylines.append(edI.pll)
                    elif self.polylinesTool in ['removepoint']:
                        if edI.pts_b.shape[0] != 0:  # Remove empty array when a polyline is completely deleted removing its points
                            self.tempPolylines.append(edI.pts_b)
                    else:
                        self.tempPolylines = edI.plls
                if event.key() == Qt.Key_D:
                    self.plot2d.setTitle('<strong><u><big><mark>D draw</strong>, J join, R remove polyline, A add point, M move point, P remove points, O offset')
                    self.polylinesTool = 'draw'
                    self.editInstance = [ptd.DrawPolyline(self.tempPolylines, self.plot2d, 10)]
                elif event.key() == Qt.Key_J:
                    self.plot2d.setTitle('D draw, <strong><u><big><mark>J join</strong>, R remove polyline, A add point, M move point, P remove points, O offset')
                    self.polylinesTool = 'join'
                    self.editInstance = [ptd.JoinPolylines(self.tempPolylines, self.plot2d, 10)]
                elif event.key() == Qt.Key_R:
                    self.plot2d.setTitle('D draw, J join, <strong><u><big><mark>R remove polyline</strong>, A add point, M move point, P remove points, O offset')
                    self.polylinesTool = 'rempoly'
                    self.editInstance = [ptd.RemovePolyline(self.tempPolylines, self.plot2d, 10)]
                elif event.key() == Qt.Key_A:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, <strong><u><big><mark>A add point</strong>, M move point, P remove points, O offset')
                    self.polylinesTool = 'addponline'
                    self.editInstance = [ptd.AddPointOnLine(pll, self.plot2d, 10) for pll in self.tempPolylines]
                elif event.key() == Qt.Key_M:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, A add point, <strong><u><big><mark>M move point</strong>, P remove points, O offset')
                    self.polylinesTool = 'movepoint'
                    self.editInstance = [ptd.MovePoint(pll, self.plot2d, 10, addline=True) for pll in self.tempPolylines]
                elif event.key() == Qt.Key_P:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, A add point, M move point, <strong><u><big><mark>P remove points</strong>, O offset')
                    self.polylinesTool = 'removepoint'
                    self.editInstance = [ptd.RemovePointsRect(pll,self.plot2d, 10, addline=True) for pll in self.tempPolylines]
                elif event.key() == Qt.Key_O:
                    self.plot2d.setTitle('D draw, J join, R remove polyline, A add point, M move point, P remove points, <strong><u><big><mark>O offset</strong>')
                    self.polylinesTool = 'offset'
                    self.lineEdit_off.setEnabled(True)
                    self.editInstance = [ptd.OffsetPolyline(self.tempPolylines,self.plot2d, 10, float(self.lineEdit_off.text()))]
            elif self.emode == 'points':
                self.plot2d.clear()
                self.tempPoints = self.editInstance[0].pts_b
                if event.key() == Qt.Key_R:
                    self.plot2d.setTitle('<strong><u><big><mark>R remove points (click)</strong>, P remove points (rect selection)')
                    self.pointsTool = 'remove'
                    self.editInstance = [ptd.RemovePointsClick(self.tempPoints, self.plot2d, 10)]
                elif event.key() == Qt.Key_P:
                    self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
                    self.pointsTool = 'removerect'
                    self.editInstance = [ptd.RemovePointsRect(self.tempPoints, self.plot2d, 10)]
            elif self.emode == 'centroids':
                self.plot2d.clear()
                self.tempCentroids = self.editInstance[0].pts_b
                if event.key() == Qt.Key_R:
                    self.plot2d.setTitle('<strong><u><big><mark>R remove points (click)</strong>, P remove points (rect selection)')
                    self.pointsTool = 'remove'
                    self.editInstance = [ptd.RemovePointsClick(self.tempCentroids, self.plot2d, 10)]
                elif event.key() == Qt.Key_P:
                    self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
                    self.pointsTool = 'removerect'
                    self.editInstance = [ptd.RemovePointsRect(self.tempCentroids, self.plot2d, 10)]
      
            for edI in self.editInstance:
                edI.start()

    
    def editMode(self):
        """ This method initializes the edit mode with a default tool
        """
        self.combo_slices.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_edit_finalize.setEnabled(True)
        self.btn_edit_discard.setEnabled(True)
        self.gui_edit_status(False)
        if self.radioPoints.isChecked():
            self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
            self.emode = 'points'
            self.pointsTool = 'removerect'
            self.tempPoints = mct.slices[mct.zcoords[self.combo_slices.currentIndex()]].copy()
            self.editInstance = [ptd.RemovePointsRect(self.tempPoints, self.plot2d, 10)]
            self.editInstance[0].start()
        elif self.radioCentroids.isChecked():
            self.plot2d.setTitle('R remove points (click), <strong><u><big><mark>P remove points (rect selection)</strong>')
            self.emode = 'centroids'
            self.pointsTool = 'removerect'
            self.tempCentroids = mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]].copy()
            self.editInstance = [ptd.RemovePointsRect(self.tempCentroids, self.plot2d, 10)]
            self.editInstance[0].start()
        elif self.radioPolylines.isChecked():
            self.plot2d.setTitle('<strong><u><big><mark>D draw</strong>, J join, R remove polyline, A add point, M move point, P remove points, O offset')
            self.emode = 'polylines'
            self.polylinesTool = 'draw'
            self.tempPolylines = mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]].copy()
            self.editInstance = [ptd.DrawPolyline(self.tempPolylines, self.plot2d, 10)]
            self.editInstance[0].start()

    
    def save_changes(self):
        """ This method exits the edit mode and updates data.
        """
        if self.emode == 'polylines':
            self.tempPolylines = []
            for edI in self.editInstance:
                edI.stop()
                if self.polylinesTool in ['addponline', 'movepoint']:
                    self.tempPolylines.append(edI.pll)
                elif self.polylinesTool in ['removepoint']:
                    if edI.pts_b.shape[0] != 0:  # Remove empty array when a polyline is completely deleted removing its points
                        self.tempPolylines.append(edI.pts_b)
                else:
                    self.tempPolylines = edI.plls      
            mct.cleanpolys[mct.zcoords[self.combo_slices.currentIndex()]] = self.tempPolylines
            self.polylinesTool = 'draw'
            self.emode = None
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            
        elif self.emode == 'points':
            for edI in self.editInstance:
                edI.stop()
            mct.slices[mct.zcoords[self.combo_slices.currentIndex()]] = self.editInstance[0].pts_b
            self.pointsTool = 'remove'
            self.emode = None
            self.status_centroids.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")

        elif self.emode == 'centroids':
            for edI in self.editInstance:
                edI.stop()
            mct.ctrds[mct.zcoords[self.combo_slices.currentIndex()]] = self.editInstance[0].pts_b
            self.pointsTool = 'remove'
            self.emode = None
            self.status_polylines.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            self.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
    
        self.combo_slices.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_edit_finalize.setEnabled(False)
        self.btn_edit_discard.setEnabled(False)
        self.gui_edit_status(True)
        self.lineEdit_off.setEnabled(False)
        self.plot2d.setTitle('')
        self.plot2d.clear()
        self.main2dplot()
    

    def discard_changes(self):
        """ This method exits the edit mode without
        altering the original data.
        """
        if self.emode == 'polylines':
            for edI in self.editInstance:
                edI.stop()
            self.polylinesTool = 'draw'
            # self.plotStaticData()
            self.emode = None
            self.tempPolylines = None
        elif self.emode == 'points' or self.emode == 'centroids':
            for edI in self.editInstance:
                edI.stop()
            self.emode = None
            self.tempPoints = None
            self.tempCentroids = None
        
        self.combo_slices.setEnabled(True)
        self.btn_edit.setEnabled(True)
        self.btn_edit_finalize.setEnabled(False)
        self.btn_edit_discard.setEnabled(False)
        self.gui_edit_status(True)
        self.lineEdit_off.setEnabled(False)
        self.plot2d.setTitle('')
        self.plot2d.clear()
        self.main2dplot()
    

    def gui_edit_status(self, torf):
        self.btn_gen_slices.setEnabled(torf)
        self.btn_gen_centr.setEnabled(torf)
        self.rbtn_fixnum.setEnabled(torf)
        self.rbtn_fixstep.setEnabled(torf)
        self.lineEdit_from.setEnabled(torf)
        self.lineEdit_to.setEnabled(torf)
        self.lineEdit_steporN.setEnabled(torf)
        self.lineEdit_thick.setEnabled(torf)
        self.menubar.setEnabled(torf)
        if mct.slices is not None:
            self.lineEdit_wall_thick.setEnabled(torf)
        if mct.ctrds is not None:
            self.btn_gen_polylines.setEnabled(torf)
        if mct.cleanpolys is not None:
            self.btn_gen_polygons.setEnabled(torf)
        if mct.polygs is not None:
            self.btn_gen_mesh.setEnabled(torf)


    def copy_polylines(self):
        copydialog = loadUi("gui_copypolylines_dialog.ui")
        copydialog.setWindowTitle("Copy slice's polylines")
        copydialog.combo_copy_pl.clear()

        for z in mct.zcoords:
            copydialog.combo_copy_pl.addItem(str('%.3f' % z))

        paste_slice = []
        for z in mct.zcoords:
            slice_index = np.where(z == mct.zcoords[:])[0][0]
            paste_slice += [QtWidgets.QCheckBox()]
            paste_slice[slice_index].setText(str('%.3f' % z))
            copydialog.scrollArea_lay.layout().addWidget(paste_slice[slice_index])

        def sel_all():
            for checkbox in paste_slice:
                checkbox.setChecked(True)

        def desel_all():
            for checkbox in paste_slice:
                checkbox.setChecked(False)

        def cancel():
            copydialog.close()

        def copy_ok():
            tocopy = mct.cleanpolys[mct.zcoords[copydialog.combo_copy_pl.currentIndex()]]
            for i in range(len(paste_slice)):
                if paste_slice[i].isChecked():
                    mct.cleanpolys[mct.zcoords[i]] = tocopy
            win.status_polygons.setStyleSheet("background-color: rgb(255, 0, 0);")
            win.status_mesh.setStyleSheet("background-color: rgb(255, 0, 0);")
            copydialog.close()

        copydialog.btn_sel_all.clicked.connect(sel_all)
        copydialog.btn_desel_all.clicked.connect(desel_all)
        copydialog.btn_cancel.clicked.connect(cancel)
        copydialog.btn_ok.clicked.connect(copy_ok)
        copydialog.exec_()


app = QApplication(sys.argv)
win = Window()
win.show()
sys.exit(app.exec_())

