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





#################################################################################
# This module contains the functions needed to interact with the plotted entities
#################################################################################
import numpy as np
import pyqtgraph as pg
from shapely.geometry import LineString



class RemovePointsClick:
    """
    Class that handles data and signals to remove points by clicking on them.
    See example 1 at the bottom of this module.
    """
    def __init__(self, pts_b, PlotItem, psz, pclr=(90, 0, 0, 255), hclr='g', verbose=False):
        self.pts_b = pts_b       # np array of points before (_b) the click event
        self.PlotItem = PlotItem # pyqtgraph plot item
        self.psz = psz           # Size of points
        self.pclr = pclr         # Color of the points
        self.hclr = hclr         # Color or the hover
        self.verbose = verbose   # If True, plots the emptying pts_b at every click
        
    def __remove_points_click(self, plot, points, ev):
        """
        plot, points and ev are automatically assigned when the function is 
        called from a signal_connect like sigClicked.connect(__remove_points_click)
        points       : list of points that have been clicked
        This private method removes the clicked points from a given array pts_b
        """
        for p in points:
            x_p = tuple(p.pos())[0]  # x coord of the clicked point
            y_p = tuple(p.pos())[1]  # y coord of the clicked point
            self.pts_b = np.delete(self.pts_b, np.where(np.logical_and(x_p == self.pts_b[:, 0], y_p == self.pts_b[:, 1])), 0)
            if self.verbose:
                print("Remaining points:\n", self.pts_b)
        self.ScatterItem.setData(self.pts_b[:, 0], self.pts_b[:, 1])
        
    def start(self):
        """
        When called, this method first creates a ScatterItem with the points
        at the initial state, then adds the ScatterItem to the PlotItem and
        finally connects the "signal emitted when a point is clicked" to the
        private method __remove_points_click()
        """
        self.ScatterItem = pg.ScatterPlotItem(
            pxMode=True,  # Set pxMode=False to allow points to transform with the view
            size=self.psz,
            brush= pg.mkBrush(self.pclr),
            hoverable=True,
            hoverPen=pg.mkPen(self.hclr, width=self.psz/15),
            hoverSize=self.psz*1.3)
        self.ScatterItem.addPoints(self.pts_b[:, 0], self.pts_b[:, 1])
        self.PlotItem.addItem(self.ScatterItem)
        self.ScatterItem.sigClicked.connect(self.__remove_points_click)
    
    def stop(self):
        """ If called, this method disables the removal of points"""

        self.ScatterItem.sigClicked.disconnect(self.__remove_points_click)



class RemovePointsRect:
    """
    Class that handles data and signals to remove points by selecting
    them with a rectangular shape. See example 2 at the bottom of this module.
    If self.addline=True, a polyline is plotted together with the points.
    """
    def __init__(self, pts_b, PlotItem, psz, addline=False, lwdth=3, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), sclr=(255, 100, 0, 45), verbose=False):
        self.pts_b = pts_b       # np array of points before (_b) the click event, or a polyline
        self.PlotItem = PlotItem # pyqtgraph plot item
        self.psz = psz           # Size of points
        self.addline = addline   # Bool to plot a polyline that connects the points
        self.lwdth = lwdth       # Width of the polyline
        self.lclr = lclr         # Color or the polyline
        self.pclr = pclr         # Color of the points
        self.sclr = sclr         # Color or the selection
        self.verbose = verbose   # If True, plots the emptying pts_b at every click
        
    def __remove_points_rect(self, event):
        """ This method removes the points inside a rectangle defined by two
        opposite vertices, i.e. the first and the second click.
        Event is given automatically from the sigMouseClicked signal
        """
        pos = event.scenePos()
        if self.click == 0:  # So this is the first click signal
            self.pos_click1 = self.PlotItem.vb.mapSceneToView(pos)  # Here I fix the coords of click1
            self.click = 1   # see start function for the meaning
            if self.verbose:
                print('First click: ', (self.pos_click1.x(), self.pos_click1.y()))
        
        elif self.click == 1:  # So this is the second click
            pos_click2 = self.PlotItem.vb.mapSceneToView(pos)
            # Remove selected points
            toremove_x = np.logical_and(self.pts_b[:, 0] >= min(self.pos_click1.x(), pos_click2.x()), self.pts_b[:, 0] <= max(self.pos_click1.x(), pos_click2.x()))
            toremove_y = np.logical_and(self.pts_b[:, 1] >= min(self.pos_click1.y(), pos_click2.y()), self.pts_b[:, 1] <= max(self.pos_click1.y(), pos_click2.y()))
            toremove = np.where(np.logical_and(toremove_x, toremove_y))
            self.pts_b = np.delete(self.pts_b, toremove, 0)
            # Refresh plot
            self.ScatterItem.setData(self.pts_b[:, 0], self.pts_b[:, 1])
            
            # Update scatter plot and polyline plot
            if self.addline:
                self.CurveItem.setData(self.pts_b[:, 0], self.pts_b[:, 1])
            
            self.temp_rect.setData(self.rectx, self.recty)
            self.line.setData(self.linex, self.liney)
            # Reset default values for counters
            self.click = 0
            self.pos_click1 = None
            if self.verbose:
                print('Second click: ', (pos_click2.x(), pos_click2.y()))
                print("Remaining points:\n", self.pts_b)
    
    def __draw_temp_rect(self, event):
        """ This method plots a transparent selection rectangle, AutoCAD style.
        """
        if self.pos_click1!= None and self.click == 1:
            pos = event  # The position for sigMouseMoved is already in Scene Coordinates
            mpos = self.PlotItem.vb.mapSceneToView(pos)  # Where the mouse is after the first click ... moving
            # Update first three sides of the rectangle
            rectx = [self.pos_click1.x(), mpos.x(), mpos.x(), self.pos_click1.x()]
            recty = [self.pos_click1.y(), self.pos_click1.y(), mpos.y(), mpos.y()]
            self.temp_rect.setData(rectx, recty)
            # Update closing line of the rectangle
            linex = [self.pos_click1.x(), self.pos_click1.x()]
            liney = [self.pos_click1.y(), mpos.y()]
            self.line.setData(linex, liney)
            
    def start(self):
        """ When called, this method plots the initial points, then plots
        a small (to hide it) rectangle and finally connects mouse signals
        to the private methods above.
        """
        # Create a plotcurve item
        if self.addline:
            self.CurveItem = pg.PlotCurveItem(
                width=self.lwdth,
                pen=pg.mkPen(color=self.lclr, width=self.lwdth))
            self.CurveItem.setData(self.pts_b[:, 0], self.pts_b[:, 1])
            self.PlotItem.addItem(self.CurveItem)
        
        # Plot points
        self.ScatterItem = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush= pg.mkBrush(self.pclr))
        self.ScatterItem.addPoints(self.pts_b[:, 0], self.pts_b[:, 1])
        self.PlotItem.addItem(self.ScatterItem)
        # Create the first three sides of the rectangle
        xfactor = self.pts_b[:, 0].mean().item()
        yfactor = self.pts_b[:, 1].mean().item()       
        self.temp_rect = pg.PlotCurveItem()
        dim = 1e-5 # Make the rectangle small to hide it
        self.rectx = np.array([0, dim, dim, 0]) + xfactor
        self.recty = np.array([0, 0, dim, dim]) + yfactor
        self.temp_rect.setData(self.rectx, self.recty)
        self.PlotItem.addItem(self.temp_rect)
        # Create the closing side of the rectangle
        self.line = pg.PlotCurveItem()
        self.linex = np.array([0, 0]) + xfactor
        self.liney = np.array([0, dim]) + yfactor
        self.line.setData(self.linex, self.liney)
        self.PlotItem.addItem(self.line)
        fill = pg.FillBetweenItem(self.temp_rect, self.line, brush=pg.mkBrush(self.sclr))
        self.PlotItem.addItem(fill)
        # Set default values of counters
        self.pos_click1 = None   # Coords of the first click
        self.click = 0           # If=0 no click has been done, if=1 the first click has been done
        # Connect signals
        self.PlotItem.scene().sigMouseMoved.connect(self.__draw_temp_rect)
        self.PlotItem.scene().sigMouseClicked.connect(self.__remove_points_rect)
    
    def stop(self):
        """ If called, this method disables the removal of points 
            through rectangular selection"""
        self.PlotItem.scene().sigMouseMoved.disconnect(self.__draw_temp_rect)
        self.PlotItem.scene().sigMouseClicked.disconnect(self.__remove_points_rect)





class MovePoint:
    """
    Class that handles data and signals to modify a polyline by clicking on
    a point and modifying its position, similarly to MovePoint class.
    See example 3 at the bottom of this module.
    """
    def __init__(self, pll, PlotItem, psz, addline=False, lwdth=3, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), hclr='g', tclr=(0, 0, 250, 255), verbose=False):
        self.pll = pll             # np array of points (or polilyne)
        self.PlotItem = PlotItem    # pyqtgraph plot item
        self.psz = psz              # Size of points
        self.addline = addline      # Bool to plot a line that connects the points
        self.lwdth = lwdth          # Line width
        self.lclr = lclr            # Color of the line
        self.pclr = pclr            # Color of the points
        self.hclr = hclr            # Color or the hover
        self.tclr = tclr            # Color of the temporary moving point
        self.verbose = verbose      # If True, plots the changing pll after the action is completed
    
    def __init_moving_point(self, plot, points, ev):
        """ plot, points and ev are automatically assigned when this private
        method is called from the sigMouseClicked signal.
        It finds the id of the clicked points, then creates a temporary list of
        points with the clicked point removed and plots it. Also, the temp node
        is plotted as well in self.TempPoint, but it will be updated by the 
        __temp_point method.
        """
        if len(points) != 1: # Do nothing if two or more points have been clicked together
            pass
        else:
            x_p = tuple(points[0].pos())[0]  # x coord of the clicked point
            y_p = tuple(points[0].pos())[1]  # y coord of the clicked point
            self.point_id = np.where(np.logical_and(x_p == self.pll[:, 0], y_p == self.pll[:, 1]))
            temp_pts = np.delete(self.pll, np.where(np.logical_and(x_p == self.pll[:, 0], y_p == self.pll[:, 1])), 0)
            self.ScatterItem.setData(temp_pts[:, 0], temp_pts[:, 1])
            self.TempPoint.addPoints([x_p], [y_p])
            self.temp_pt = np.array([x_p, y_p])
            self.click = 1
            self.conflict1 = True
            # Connect signal for temporary point
            self.PlotItem.scene().sigMouseMoved.connect(self.__temp_point)
    
    def __finalize_moving_point(self, event):
        """The event parameter is automatically assigned by calling through the signal.
        The position of the second click is obtained, then the point under the first
        click is substituded by the position under the second click.
        Finally the plot is updated and the mousemoved signal is disconnected.
        If self.addline=True, the final shape of the polyline is set as well.
        """
        pos = event.scenePos()
        if self.click == 0:  # So this is the first click signal
            pass
        elif self.click == 1:
            pos_click2 = self.PlotItem.vb.mapSceneToView(pos)
            x_p = pos_click2.x()
            y_p = pos_click2.y()
            # Handle the conflict that happens because with the first click
            # a sigMouseClicked is sent together with scatter.sigClicked
            tol = 1e-5
            if np.absolute(x_p - self.temp_pt[0]) > tol and np.absolute(y_p - self.temp_pt[1]) > tol and self.conflict1==True:
                self.conflict1 = False
            else:
                # Update np array with the final position of the moved point
                self.pll[self.point_id[0][0]] = np.array([x_p, y_p])
                if self.verbose:
                    print(self.pll)
                # Update scatter plot and polyline plot
                self.ScatterItem.setData(self.pll[:, 0], self.pll[:, 1])
                if self.addline:
                    self.CurveItem.setData(self.pll[:, 0], self.pll[:, 1])
                # Set default values and clear
                self.click = 0
                self.temp_pt = None
                self.TempPoint.clear()
                # Disconnect signal for temporary point
                self.PlotItem.scene().sigMouseMoved.disconnect(self.__temp_point)
    
    def __temp_point(self, event):
        """ After a first click has been registered, this private method plots 
        a temporary moving point (point dragged by te mouse). The temp point 
        disappears after the second click.
        If self.addline=True, it also updates the polyline while the point is moving.
        """
        if self.click == 1:
            pos = event  # The position for sigMouseMoved is already in Scene Coordinates
            mpos = self.PlotItem.vb.mapSceneToView(pos)  # Where the mouse is after the first click ... moving
            # Update the position of the temp moving point
            self.TempPoint.setData([mpos.x()], [mpos.y()])
            # Update the shape of the polyline
            if self.addline:
                temp_pll = self.pll
                temp_pll[self.point_id[0][0]] = np.array([mpos.x(), mpos.y()])
                self.CurveItem.setData(temp_pll[:, 0], temp_pll[:, 1])
    
    def start(self):
        """ When called, this method plots the initial points throuth self.ScatterItem,
        then initializes the pg.ScatterPlotItem for the temporary point, then 
        assigns default value for useful variables and finally connects the signals to two
        of the private methods above.
        If self.addline=True, it also plots the polyline that connects the points.
        """
        # Create a plotcurve item
        if self.addline:
            self.CurveItem = pg.PlotCurveItem(
                width=self.lwdth,
                pen=pg.mkPen(color=self.lclr, width=self.lwdth))
            self.CurveItem.setData(self.pll[:, 0], self.pll[:, 1])
            self.PlotItem.addItem(self.CurveItem)
        # Create scatter item for static points
        self.ScatterItem = pg.ScatterPlotItem(
            pxMode=True,  # Set pxMode=False to allow points to transform with the view
            size=self.psz,
            brush= pg.mkBrush(self.pclr),
            hoverable=True,
            hoverPen=pg.mkPen(self.hclr, width=self.psz/15),
            hoverSize=self.psz*1.3)
        self.PlotItem.addItem(self.ScatterItem)
        self.ScatterItem.addPoints(self.pll[:, 0], self.pll[:, 1])
        # Create scatter item for the temp moving point
        self.TempPoint = pg.ScatterPlotItem(
            pxMode=True,  # Set pxMode=False to allow points to transform with the view
            size=self.psz,
            brush= pg.mkBrush(self.tclr),
            hoverable=True,
            hoverPen=pg.mkPen(self.hclr, width=self.psz/15),
            hoverSize=self.psz*1.3)
        self.PlotItem.addItem(self.TempPoint)
        # Set default values for counters
        self.temp_pt = None
        self.click = 0
        # Connect signals
        self.ScatterItem.sigClicked.connect(self.__init_moving_point)
        self.PlotItem.scene().sigMouseClicked.connect(self.__finalize_moving_point)
    
    def stop(self):
        """ If called, this method disconnects all the signals """
        self.ScatterItem.sigClicked.disconnect(self.__init_moving_point)
        self.PlotItem.scene().sigMouseClicked.disconnect(self.__finalize_moving_point)
        try:
            self.PlotItem.scene().sigMouseMoved.disconnect(self.__temp_point)
        except TypeError:
            if self.verbose:
                print('sigMouseMoved was already disconnected... all good!')





class AddPointOnLine:
    """
    Class that handles data and signals to add a point in a polyline
    See example 4 at the bottom of this module.
    """
    def __init__(self, pll, PlotItem, psz, lwdth=5, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), hclr='g', hlclr=(0, 255, 70, 255), verbose=False):
        self.pll = pll              # np array of points (or polilyne)
        self.PlotItem = PlotItem    # pyqtgraph plot item
        self.psz = psz              # Size of points
        self.lwdth = lwdth          # Line width
        self.lclr = lclr            # Color of the line
        self.pclr = pclr            # Color of the points
        self.hclr = hclr            # Color or the hover
        self.hlclr = hlclr          # Color of the line when the mouse is on it (hover)
        self.verbose = verbose      # If True, plots the changing pll after the action is completed
    
    def __getSegment(self, event):
        """ This method changes the color of the segment under the mouse pointer and 
        then saves the key of the dictionary self.segments in self.tomodify
        """
        pos = event  # The position for sigMouseMoved is already in Scene Coordinates
        mpos = self.PlotItem.vb.mapSceneToView(pos)  # Mouse position
        # Highlight the element under the mouse pointer and save its key in self.tomodify
        if self.invisible_polyline.mouseShape().contains(mpos):
            found = False  # Counter to avoid selecting two segments together
            discarded = 0
            for key in self.segments:
                if self.segments[key][0].mouseShape().contains(mpos) and found == False:
                    self.segments[key][0].setPen(pg.mkPen(color=self.hlclr, width=self.lwdth*1.3))
                    self.tomodify = key  # Dict's key of the selected segment where to add a point (after a click)
                    found = True
                else:
                    self.segments[key][0].setPen(pg.mkPen(color=self.lclr, width=self.lwdth))
                    discarded += 1
                if discarded == len(self.segments):
                    self.tomodify = None
            found = False
        else:
            self.tomodify = None
    
    def __addPoint(self, event):
        """ This method adds the position of the click in the np array 
        of the polyline self.pll
        """
        if self.tomodify is not None:  # self.tomodify is set in __getSegment method
            # Get click position
            pos = event.scenePos()
            pos_click = self.PlotItem.vb.mapSceneToView(pos)
            x_p = pos_click.x()
            y_p = pos_click.y()
            # Insert the click position in the middle of the selected segment
            self.segments[self.tomodify][1] = np.insert(self.segments[self.tomodify][1], 1, [x_p, y_p], axis=0)
            # Use the segments (only one of them is updated and has 3 points) to reassemble the polyline
            tempstack = np.array([[None, None]])
            for key in self.segments:
                tempstack = np.vstack((tempstack, self.segments[key][1]))
            tempstack = np.delete(tempstack, 0, axis=0).astype(dtype=np.float32, copy=False)            
            newpolyline = np.array([[None, None]]).astype(dtype=np.float32, copy=False)
            for row in tempstack:
                if np.any(row != newpolyline[-1]):
                    newpolyline = np.vstack((newpolyline, row))
                else:
                    continue
            newpolyline = np.delete(newpolyline, 0, axis=0)
            # Update the polyline attribute self.pll with the new reassembled one
            self.pll = newpolyline.astype(dtype=np.float32, copy=False)
            if self.verbose:
                print("\n\nMODIFIED\n", self.pll)
            # Clean up the plot and segments dictionary
            for key in self.segments:
                self.PlotItem.removeItem(self.segments[key][0])
            self.PlotItem.removeItem(self.invisible_polyline)
            self.PlotItem.removeItem(self.ScatterItem)
            self.segments = {}
            # Setup again segments and plot
            self.__setupItems()
    
    def __refresh_clickable_area(self):
        """ This method solves the problem that happen when after a point has
        been added with a lot of zoom, it is not possible to click on the segment
        if the user zooms out.
        """
        # Get ViewBox's viewrange info
        vbstate = self.PlotItem.vb.getState(copy=True)
        viewrange = vbstate['viewRange']
        new_xwidth = viewrange[0][1] - viewrange[0][0]
        # Update everything only if the user has zoomed more than a threshold
        if np.absolute((self.xwidth - new_xwidth) / self.xwidth) > 0.55:
            # Disconnect signals to avoid problems (Maybe useless)
            self.PlotItem.scene().sigMouseMoved.disconnect(self.__getSegment)
            self.PlotItem.scene().sigMouseClicked.disconnect(self.__addPoint)
            # Update self.xwidth
            self.xwidth = new_xwidth
            # Clean up plot and populate it again (through __setupItems)
            for key in self.segments:
                self.PlotItem.removeItem(self.segments[key][0])
            self.PlotItem.removeItem(self.invisible_polyline)
            self.PlotItem.removeItem(self.ScatterItem)
            self.segments = {}
            self.__setupItems()
            # Reconnect signals
            self.PlotItem.scene().sigMouseMoved.connect(self.__getSegment)
            self.PlotItem.scene().sigMouseClicked.connect(self.__addPoint)

    def __setupItems(self):
        """ This method creates a dict of segments from the polyline and
        plots them and the points at the vertices of the polyline.
        """
        # Create a dict with key=int, value=[PlotCurveItem, segment=np.array 2x2]
        self.segments = {}
        for i in range(self.pll.shape[0]-1):
            x = np.array([self.pll[i, 0], self.pll[i+1, 0]])
            y = np.array([self.pll[i, 1], self.pll[i+1, 1]])
            CurveItem = pg.PlotCurveItem(
            pen=pg.mkPen(color=self.lclr, width=self.lwdth))
            CurveItem.setClickable(False, width=7)
            #### CurveItem.setSkipFiniteCheck(True)   ## Needed recent version of pyqtgraph
            CurveItem.setData(x, y)
            self.PlotItem.addItem(CurveItem)
            xy = np.hstack((x.reshape(2, 1), y.reshape(2, 1))).astype(dtype=np.float32, copy=False)
            self.segments[i] = [CurveItem, xy]
            
        # This invisible_polyline avoids to keep looping
        # on all the segments when the mouse is far from the polyline
        self.invisible_polyline = pg.PlotCurveItem(
            pen=pg.mkPen((255, 255, 0, 0), width=1))
        self.invisible_polyline.setClickable(False, width=100)
        self.PlotItem.addItem(self.invisible_polyline)
        self.invisible_polyline.setData(self.pll[:, 0], self.pll[:, 1])
        # Plot points at the vertices of the polyline
        self.ScatterItem = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush= pg.mkBrush(self.pclr))
        self.ScatterItem.addPoints(self.pll[:, 0], self.pll[:, 1])
        self.PlotItem.addItem(self.ScatterItem)

    def start(self):
        """ This method starts everything just as the other classes above.
        Call it after an instance of this class has been created.
        """
        # Change the np array type, maybe needed only if input data
        # is a test array of integers
        self.pll = self.pll.astype(dtype=np.float32, copy=False)
        if self.verbose:
            print("\n\n\nINITIAL\n", self.pll)
        # Initialize plots and data and connect signals
        self.__setupItems()
        self.PlotItem.scene().sigMouseMoved.connect(self.__getSegment)
        self.PlotItem.scene().sigMouseClicked.connect(self.__addPoint)
        self.PlotItem.sigRangeChanged.connect(self.__refresh_clickable_area)
        # Get initial viewrange of the ViewBox, needed only for
        # __refresh_clickable_area method
        vbstate = self.PlotItem.vb.getState(copy=True)
        viewrange = vbstate['viewRange']
        self.xwidth = viewrange[0][1] - viewrange[0][0]
        
    def stop(self):
        """ If called, this method disconnects all the signals """
        self.PlotItem.scene().sigMouseMoved.disconnect(self.__getSegment)
        self.PlotItem.scene().sigMouseClicked.disconnect(self.__addPoint)
        self.PlotItem.sigRangeChanged.disconnect(self.__refresh_clickable_area)





class RemovePolyline:
    """
    Class that handles data and signals to remove a polyline given a list that
    contains one or more polylines as np arrays.
    See example 5 at the bottom of this module.
    """
    def __init__(self, plls, PlotItem, psz, lwdth=5, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), hclr='g', hlclr=(0, 255, 70, 255), verbose=False):
        self.plls = plls              # list containing np arrays of polylines
        self.PlotItem = PlotItem    # pyqtgraph plot item
        self.psz = psz              # Size of points
        self.lwdth = lwdth          # Line width
        self.lclr = lclr            # Color of the line
        self.pclr = pclr            # Color of the points
        self.hclr = hclr            # Color or the hover
        self.hlclr = hlclr          # Color of the line when the mouse is on it (hover)
        self.verbose = verbose      # If True, plots the changing pll after the action is completed
    
    def __getPolyline(self, event):
        """ This method changes the color of the pollyline under the mouse pointer and 
        then saves the key of the dictionary self.CurveItem (corresponding to the index of
        the self.plls item that has to be removed) in self.tomodify
        """
        pos = event  # The position for sigMouseMoved is already in Scene Coordinates
        mpos = self.PlotItem.vb.mapSceneToView(pos)  # Mouse position
        # Highlight the element under the mouse pointer and save its key in self.tomodify
        if self.invisible_polyline.mouseShape().contains(mpos):
            found = False  # Counter to avoid selecting two segments together
            discarded = 0
            for key in self.CurveItems:
                if self.CurveItems[key].mouseShape().contains(mpos) and found == False:
                    self.CurveItems[key].setPen(pg.mkPen(color=self.hlclr, width=self.lwdth*1.3))
                    self.tomodify = key  # Dict's key of the selected segment where to add a point (after a click)
                    found = True
                else:
                    self.CurveItems[key].setPen(pg.mkPen(color=self.lclr, width=self.lwdth))
                    discarded += 1
                if discarded == len(self.CurveItems):
                    self.tomodify = None
            found = False
        else:
            self.tomodify = None
    
    def __popPolyline(self, event):
        """ This method removes the clicked polyline from the list self.plls 
        through the standard python pop method, then refreshes everything.
        """
        if self.tomodify is not None:  # self.tomodify is set in __Polyline method
            # Disconnect signal for refresh function to avoid plot problems
            self.PlotItem.sigRangeChanged.disconnect(self.__refresh_clickable_area)
            # Remove the clicked polyline from the list
            self.plls.pop(self.tomodify)
            # Update the polyline attribute self.pll with the new reassembled one
            if self.verbose:
                print("\nNew number of polylines: ", len(self.plls))
            # Clean up the plot and CurveItems dictionary
            for key in self.CurveItems:
                self.PlotItem.removeItem(self.CurveItems[key])
            self.PlotItem.removeItem(self.invisible_polyline)
            self.PlotItem.removeItem(self.ScatterItem)
            self.CurveItems = {}
            # Setup again plot and data
            self.__setupItems()
            # Reconnect signal
            self.PlotItem.sigRangeChanged.connect(self.__refresh_clickable_area)
    
    def __refresh_clickable_area(self):
        """ This method solves the problem that happen when after a point has
        been added with a lot of zoom, it is not possible to click on the segment
        if the user zooms out.
        
        !! For this RemovePolyline class this method could be disconnected
        to improve performances, or maybe just set a higher threshold !!
        """
        # Get ViewBox's viewrange info
        vbstate = self.PlotItem.vb.getState(copy=True)
        viewrange = vbstate['viewRange']
        new_xwidth = viewrange[0][1] - viewrange[0][0]
        # Update everything only if the user has zoomed more than a threshold
        if np.absolute((self.xwidth - new_xwidth) / self.xwidth) > 0.7:
            # Disconnect signals to avoid problems (Maybe useless)
            self.PlotItem.scene().sigMouseMoved.disconnect(self.__getPolyline)
            self.PlotItem.scene().sigMouseClicked.disconnect(self.__popPolyline)
            # Update self.xwidth
            self.xwidth = new_xwidth
            # Clean up plot and populate it again (through __setupItems)
            for key in self.CurveItems:
                self.PlotItem.removeItem(self.CurveItems[key])
            self.PlotItem.removeItem(self.invisible_polyline)
            self.PlotItem.removeItem(self.ScatterItem)
            self.CurveItems = {}
            self.__setupItems()
            # Reconnect signals
            self.PlotItem.scene().sigMouseMoved.connect(self.__getPolyline)
            self.PlotItem.scene().sigMouseClicked.connect(self.__popPolyline)

    def __setupItems(self):
        """ This method creates a dict of curveitems from the polylines and
        plots them and the points at the vertices of the polyline.
        """
        try:
            # Create a dict with key=int corresponding to the self.plls index
            # and value = PlotCurveItem_ith
            self.CurveItems = {}
            for i in range(len(self.plls)):
                CurveItem = pg.PlotCurveItem(
                pen=pg.mkPen(color=self.lclr, width=self.lwdth))
                CurveItem.setClickable(False, width=7)
                #### CurveItem.setSkipFiniteCheck(True)   ## Needed recent version of pyqtgraph
                CurveItem.setData(self.plls[i][:, 0], self.plls[i][:, 1])
                self.PlotItem.addItem(CurveItem)
                self.CurveItems[i] = CurveItem
                
            # This invisible_polyline avoids to keep looping
            # on all the polylines when the mouse pointer is far from them
            polylines_linked = self.plls[0]
            for pll in self.plls[1:]:
                polylines_linked = np.vstack((polylines_linked, pll))
            self.invisible_polyline = pg.PlotCurveItem(
                pen=pg.mkPen((255, 255, 0, 0), width=1))
            self.invisible_polyline.setClickable(False, width=100)
            self.invisible_polyline.setData(polylines_linked[:, 0], polylines_linked[:, 1])
            self.PlotItem.addItem(self.invisible_polyline)
            # Plot points at the vertices of the polylines
            self.ScatterItem = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush= pg.mkBrush(self.pclr))
            self.ScatterItem.addPoints(polylines_linked[:, 0], polylines_linked[:, 1])
            self.PlotItem.addItem(self.ScatterItem)
        except IndexError:
            print('\nNo more polylines to delete!')

    def start(self):
        """ This method starts everything just as the other classes above.
        Call it after an instance of this class has been created.
        """
        if self.verbose:
            print("\nInitial number of polylines: ", len(self.plls))
            print(self.plls)
        # Initialize plots and data and connect signals
        self.__setupItems()
        self.PlotItem.scene().sigMouseMoved.connect(self.__getPolyline)
        self.PlotItem.sigRangeChanged.connect(self.__refresh_clickable_area)
        self.PlotItem.scene().sigMouseClicked.connect(self.__popPolyline)
        # Get initial viewrange of the ViewBox, needed only for
        # __refresh_clickable_area method
        vbstate = self.PlotItem.vb.getState(copy=True)
        viewrange = vbstate['viewRange']
        self.xwidth = viewrange[0][1] - viewrange[0][0]
        
    def stop(self):
        """ If called, this method disconnects all the signals """
        self.PlotItem.scene().sigMouseMoved.disconnect(self.__getPolyline)
        self.PlotItem.sigRangeChanged.disconnect(self.__refresh_clickable_area)
        self.PlotItem.scene().sigMouseClicked.disconnect(self.__popPolyline)





class DrawPolyline:
    """
    Class that handles data and signals to draw a new polyline.
    See example 6 at the bottom of this module.
    """
    def __init__(self, plls, PlotItem, psz, lwdth=3, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), hclr='g', verbose=False):
        self.plls = plls            # List of np arrays of existing polylines
        self.PlotItem = PlotItem    # pyqtgraph plot item
        self.psz = psz              # Size of points
        self.lwdth = lwdth          # Line width
        self.lclr = lclr            # Color of the line
        self.pclr = pclr            # Color of the points
        self.hclr = hclr            # Color or the hover of the last point used to finalize
        self.verbose = verbose      # If True, plots the changing pll after the action is completed

    def __draw_points(self, event):
        """ This method takes the click to draw a point, then adds its coords
        to the points_list... lists and updates the plot.
        """
        if self.hovered == False:  # Condition to avoid conflict with sigClicked from clickable_point 
            pos = event.scenePos()
            click_coords = self.PlotItem.vb.mapSceneToView(pos)
            self.points_list_x.append(click_coords.x())
            self.points_list_y.append(click_coords.y())
            self.clickable_point.clear()
            self.line_between.clear()
            self.temp_line.clear()
            
            if len(self.points_list_x) >= 2:
                self.line_between.setData(self.points_list_x, self.points_list_y)
                self.drawn_points.setData(self.points_list_x[:-1], self.points_list_y[:-1])
                self.clickable_point.setData([self.points_list_x[-1]], [self.points_list_y[-1]])
            elif len(self.points_list_x) == 1:
                self.drawn_points.setData(self.points_list_x, self.points_list_y)

    def __draw_temp_line(self, event):
        """ This method draws the moving line between the last drawn point and the 
        mouse pointer.
        """
        self.hovered = False  # Set condition to avoid conflict with sigClicked from clickable_point 
        pos = event
        mouse_coords = self.PlotItem.vb.mapSceneToView(pos)
        if len(self.points_list_x) >= 1:
            self.temp_line.clear()
            xx = [self.points_list_x[-1]]
            xx.append(mouse_coords.x())
            yy = [self.points_list_y[-1]]
            yy.append(mouse_coords.y())
            self.temp_line.setData(xx, yy)

    def __hovered(self):
        """ This method, connected with self.clickable_point.sigHovered.connect(self.__hovered),
        is needed only to avoid a conflict that happens because the sigClicked of the
        clicking on the clickable_point is emitted together with the sigMouseClicked
        of the self.PlotItem.
        """
        self.hovered = True

    def __finalize(self, plot, points, ev):
        """ This method takes the new drawn polylines and adds it to the initial
        self.plls list of static polylines, then refreshes everything.
        """
        self.hovered = True
        # Add polyline to initial list
        plen = len(self.points_list_x)
        newpolyline = np.hstack((np.array(self.points_list_x).reshape(plen, 1), np.array(self.points_list_y).reshape(plen, 1)))
        self.plls.append(newpolyline)
        # Refresh plot
        self.drawn_points.clear()
        self.clickable_point.clear()
        self.line_between.clear()
        self.temp_line.clear()
        self.__setStaticItems()
        if self.verbose:
            print('Updated number of polylines: ', len(self.plls))
            print("New polyline:\n", newpolyline)
        # Set default data
        self.points_list_x = []
        self.points_list_y = []

    def __setStaticItems(self):
        """ This method sets up and plots the initial given static polylines
        in self.plls.
        """
        # Create a dict with key=int corresponding to the self.plls index
        # and value = PlotCurveItem_ith
        self.CurveItems = {} # At the end I did't use this dictionary, have to check if something can be simplified
        for i in range(len(self.plls)):
            CurveItem = pg.PlotCurveItem(
            pen=pg.mkPen(color=self.lclr, width=self.lwdth))
            #### CurveItem.setSkipFiniteCheck(True)   ## Needed recent version of pyqtgraph
            CurveItem.setData(self.plls[i][:, 0], self.plls[i][:, 1])
            self.PlotItem.addItem(CurveItem)
            self.CurveItems[i] = CurveItem
        # Here the insivible polyline is used to plot
        # all the vertices using only one ScatterPlotItem
        polylines_linked = self.plls[0]
        for pll in self.plls[1:]:
            polylines_linked = np.vstack((polylines_linked, pll))
        # Plot points at the vertices of the polylines
        self.ScatterItem = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush=pg.mkBrush(self.pclr))
        self.ScatterItem.setData(polylines_linked[:, 0], polylines_linked[:, 1])
        self.PlotItem.addItem(self.ScatterItem)

    def start(self):
        """ This method starts everything just as the other classes above.
        Call it after an instance of this class has been created.
        """
        # Call private method to setup data and add to the plot the existing not editable polylines
        self.__setStaticItems()
        if self.verbose:
            print('Initial number of polylines: ', len(self.plls))
        # Create empty items that will be used by the drawing functions       
        light_lclr = list(self.lclr)
        light_lclr[3] = 100
        light_lclr = tuple(light_lclr)
        self.line_between = pg.PlotCurveItem(pen=pg.mkPen(color=light_lclr, width=self.lwdth))
        self.PlotItem.addItem(self.line_between)
        self.temp_line = pg.PlotCurveItem(pen=pg.mkPen(color=light_lclr, width=self.lwdth))
        self.PlotItem.addItem(self.temp_line)
        self.drawn_points = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush= pg.mkBrush(self.pclr))
        self.PlotItem.addItem(self.drawn_points)
        self.clickable_point = pg.ScatterPlotItem(pxMode=True, size=1.5*self.psz, brush= pg.mkBrush(self.pclr),
                                                  hoverable=True, hoverPen=pg.mkPen(self.hclr, width=self.psz/10), hoverSize=self.psz*1.3)
        self.clickable_point.setSymbol('+')
        self.PlotItem.addItem(self.clickable_point)
        # Set default data
        self.points_list_x = []
        self.points_list_y = []
        self.hovered = False
        # Connect signals
        self.PlotItem.scene().sigMouseClicked.connect(self.__draw_points)
        self.PlotItem.scene().sigMouseMoved.connect(self.__draw_temp_line)
        self.clickable_point.sigClicked.connect(self.__finalize)
        self.clickable_point.sigHovered.connect(self.__hovered)
        
    def stop(self):
        """ If called, this method disconnects all the signals """
        self.PlotItem.scene().sigMouseClicked.disconnect(self.__draw_points)
        self.PlotItem.scene().sigMouseMoved.disconnect(self.__draw_temp_line)
        self.clickable_point.sigClicked.disconnect(self.__finalize)
        self.clickable_point.sigHovered.disconnect(self.__hovered)





class JoinPolylines:
    """
    Class that handles data and signals to join two polylines by clicking
    on their end points.
    See example 7 at the bottom of this module.
    """
    def __init__(self, plls, PlotItem, psz, lwdth=3, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), hclr='g', verbose=False):
        self.plls = plls            # List of np arrays of existing polylines
        self.PlotItem = PlotItem    # pyqtgraph plot item
        self.psz = psz              # Size of points
        self.lwdth = lwdth          # Line width
        self.lclr = lclr            # Color of the line
        self.pclr = pclr            # Color of the points
        self.hclr = hclr            # Color or the hover of the last point used to finalize
        self.verbose = verbose      # If True, plots the changing pll after the action is completed
           
    def __join_polylines(self, plot, points, ev):
        """ For click one, this method stores info about the clicked point, which
        polyline it belongs to and if it is a head or a tail vertex. The clickable
        extreme points are updated as well to avoid conflicts.
        With click two, info are got as clic one, then the two polylines are joined
        and finally the plot and signals are refreshed.
        """
        if points.shape[0] == 1:
            if self.first_poly is None:
                # Indentify and store info of the first polyline and its clicked point
                x_p = tuple(points[0].pos())[0]  # x coord of the clicked point
                y_p = tuple(points[0].pos())[1]  # y coord of the clicked point
                for i in range(len(self.plls)):
                    if [x_p, y_p] in self.plls[i].tolist():
                        self.first_poly = [i, self.plls[i].tolist().index([x_p, y_p])]
                        
                # Refresh the extreme_points to avoid clicking again on the first_poly
                self.extreme_points.clear()
                for i in range(len(self.plls)):
                    if i != self.first_poly[0]:                   
                        self.extreme_points.addPoints([self.plls[i][0, 0], self.plls[i][-1, 0]], [self.plls[i][0, 1], self.plls[i][-1, 1]])
                        
            elif self.first_poly is not None:
                # Indentify and store info of the second polyline and its clicked point
                x_p = tuple(points[0].pos())[0]
                y_p = tuple(points[0].pos())[1]
                for i in range(len(self.plls)):
                    if [x_p, y_p] in self.plls[i].tolist():
                        self.second_poly = [i, self.plls[i].tolist().index([x_p, y_p])]
                
                # Join the two polylines
                if self.first_poly[1] != 0 and self.second_poly[1] == 0:
                    newpolyline = np.vstack((self.plls[self.first_poly[0]], self.plls[self.second_poly[0]]))
                elif self.first_poly[1] != 0 and self.second_poly[1] != 0:
                    newpolyline = np.vstack((self.plls[self.first_poly[0]], np.flip(self.plls[self.second_poly[0]], axis=0)))
                elif self.first_poly[1] == 0 and self.second_poly[1] == 0:
                    newpolyline = np.vstack((np.flip(self.plls[self.first_poly[0]], axis=0), self.plls[self.second_poly[0]]))
                if self.first_poly[1] == 0 and self.second_poly[1] != 0:
                    newpolyline = np.vstack((self.plls[self.second_poly[0]], self.plls[self.first_poly[0]]))
                
                # Remove the two original polylines
                to_remove = [self.plls[self.first_poly[0]].tolist(), self.plls[self.second_poly[0]].tolist()]
                self.plls = [pll for pll in self.plls if pll.tolist() not in to_remove]
                # Append new joined polyline to the plls list
                self.plls.append(newpolyline)
                # Set default values
                self.first_poly = None
                self.second_poly = None
                # Clear plot
                self.extreme_points.clear()
                self.ScatterItem.clear()
                for key in self.CurveItems:
                    self.CurveItems[key].clear()
                self.CurveItems = {}
                # Refresh plot and signals
                self.extreme_points.sigClicked.disconnect(self.__join_polylines)
                self.__setItems()
                self.extreme_points.sigClicked.connect(self.__join_polylines)
                if self.verbose:
                    print("Updated number of polylines: ", len(self.plls))

    def __setItems(self):
        """ This method sets up and plots the initial given polylines
        stored in self.plls.
        """
        # Create a dict with key=int corresponding to the self.plls index
        self.CurveItems = {} 
        self.extreme_points = pg.ScatterPlotItem(pxMode=True, size=1.5*self.psz, brush= pg.mkBrush(self.pclr),
                                          hoverable=True, hoverPen=pg.mkPen(self.hclr, width=self.psz/10), hoverSize=self.psz*1.3)
        self.extreme_points.setSymbol('d')       
        for i in range(len(self.plls)):
            # Create and plot polylines, first and last point items
            CurveItem = pg.PlotCurveItem(
            pen=pg.mkPen(color=self.lclr, width=self.lwdth))
            #### CurveItem.setSkipFiniteCheck(True)   ## Needed recent version of pyqtgraph
            CurveItem.setData(self.plls[i][:, 0], self.plls[i][:, 1])
            self.PlotItem.addItem(CurveItem)
            self.extreme_points.addPoints([self.plls[i][0, 0], self.plls[i][-1, 0]], [self.plls[i][0, 1], self.plls[i][-1, 1]])
            # Store plot items in the dictionary
            self.CurveItems[i] = CurveItem
            
        self.PlotItem.addItem(self.extreme_points)
        # Here the insivible polyline is used to plot
        # the vertices (except first and last) using only one ScatterPlotItem
        polylines_linked = self.plls[0][1:-1]
        for pll in self.plls[1:]:
            polylines_linked = np.vstack((polylines_linked, pll[1:-1]))
        # Plot points at the vertices of the polylines (except first and last)
        self.ScatterItem = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush=pg.mkBrush(self.pclr))
        self.ScatterItem.setData(polylines_linked[:, 0], polylines_linked[:, 1])
        self.PlotItem.addItem(self.ScatterItem)

    def start(self):
        """ This method starts everything just as the other classes above.
        Call it after an instance of this class has been created.
        """
        # Call private method to setup data and add to the plot the existing not editable polylines
        self.__setItems()
        if self.verbose:
            print('Initial number of polylines: ', len(self.plls))
        self.first_poly = None  # It will be set as [index of self.plls list, 0 for head and 1 for tail]
        self.second_poly = None # Same as above,    
        # Connect signal
        self.extreme_points.sigClicked.connect(self.__join_polylines)
        
    def stop(self):
        """ If called, this method disconnects all the signals """
        self.extreme_points.sigClicked.disconnect(self.__join_polylines)







class OffsetPolyline:
    """
    Class that handles data and signals to do the offset of a polyline given a 
    list that contains one or more polylines as np arrays.
    See example 5 at the bottom of this module.
    """
    def __init__(self, plls, PlotItem, psz, offset, lwdth=5, lclr=(0, 100, 200, 255), pclr=(90, 0, 0, 255), hclr='g', hlclr=(0, 255, 70, 255), verbose=False):
        self.plls = plls            # list containing np arrays of polylines
        self.PlotItem = PlotItem    # pyqtgraph plot item
        self.psz = psz              # Size of points
        self.offset = offset        # Offset: positive -> right, negative -> left
        self.lwdth = lwdth          # Line width
        self.lclr = lclr            # Color of the line
        self.pclr = pclr            # Color of the points
        self.hclr = hclr            # Color or the hover
        self.hlclr = hlclr          # Color of the line when the mouse is on it (hover)
        self.verbose = verbose      # If True, plots the changing pll after the action is completed
    
    def __getPolyline(self, event):
        """ This method changes the color of the pollyline under the mouse pointer and 
        then saves the key of the dictionary self.CurveItem (corresponding to the index of
        the self.plls item that has to be removed) in self.tomodify
        """
        self.setSide()
        pos = event  # The position for sigMouseMoved is already in Scene Coordinates
        mpos = self.PlotItem.vb.mapSceneToView(pos)  # Mouse position
        # Highlight the element under the mouse pointer and save its key in self.tomodify
        if self.invisible_polyline.mouseShape().contains(mpos):
            found = False  # Counter to avoid selecting two segments together
            discarded = 0
            for key in self.CurveItems:
                if self.CurveItems[key].mouseShape().contains(mpos) and found == False:
                    self.CurveItems[key].setPen(pg.mkPen(color=self.hlclr, width=self.lwdth*1.3))
                    self.tomodify = key  # Dict's key of the selected segment where to add a point (after a click)
                    # Draw temporary offset polyline
                    try:
                        tempOff = np.array(LineString(self.plls[self.tomodify]).parallel_offset(np.absolute(self.offset), side=self.side, resolution=5, join_style=2, mitre_limit=5))
                        self.tempOff.setData(tempOff[:, 0], tempOff[:, 1])
                    except IndexError:
                        continue  # Probably this error happens because of weird data collected by mistake by the mouse
                    found = True
                else:
                    self.CurveItems[key].setPen(pg.mkPen(color=self.lclr, width=self.lwdth))
                    discarded += 1
                if discarded == len(self.CurveItems):
                    self.tomodify = None
            found = False
        else:
            self.tomodify = None
            self.tempOff.clear()

            
    
    def __offPolyline(self, event):
        """ This method removes the clicked polyline from the list self.plls 
        through the standard python pop method, then refreshes everything.
        """
        self.setSide
        
        if self.tomodify is not None:  # self.tomodify is set in __Polyline method
            # Disconnect signal for refresh function to avoid plot problems
            self.PlotItem.sigRangeChanged.disconnect(self.__refresh_clickable_area)
            # Create new offset polyline and add it to the initial list of polylines
            
            
            newpoly = np.array(LineString(self.plls[self.tomodify]).parallel_offset(np.absolute(self.offset), side=self.side, resolution=5, join_style=2, mitre_limit=5))
            if len(newpoly) >= 2:  # Offset of a closed polyline could result in a empty array
                if self.side == 'left':
                    self.plls.append(newpoly)
                elif self.side == 'right':  # Shapely flips the array if side == right
                    self.plls.append(np.flip(newpoly, axis=0))
            
            # Update the polyline attribute self.pll with the new reassembled one
            if self.verbose:
                print("\nNew number of polylines: ", len(self.plls))
            # Clean up the plot and CurveItems dictionary
            for key in self.CurveItems:
                self.PlotItem.removeItem(self.CurveItems[key])
            self.PlotItem.removeItem(self.invisible_polyline)
            self.PlotItem.removeItem(self.ScatterItem)
            self.CurveItems = {}
            # Setup again plot and data
            self.__setupItems()
            # Reconnect signal
            self.PlotItem.sigRangeChanged.connect(self.__refresh_clickable_area)
            
    
    def __refresh_clickable_area(self):
        """ This method solves the problem that happen when after a point has
        been added with a lot of zoom, it is not possible to click on the segment
        if the user zooms out.
        
        !! For this RemovePolyline class this method could be disconnected
        to improve performances, or maybe just set a higher threshold !!
        (comment copied from RemovePolyline, should be ok)
        """
        # Get ViewBox's viewrange info
        vbstate = self.PlotItem.vb.getState(copy=True)
        viewrange = vbstate['viewRange']
        new_xwidth = viewrange[0][1] - viewrange[0][0]
        # Update everything only if the user has zoomed more than a threshold
        if np.absolute((self.xwidth - new_xwidth) / self.xwidth) > 0.7:
            # Disconnect signals to avoid problems (Maybe useless)
            self.PlotItem.scene().sigMouseMoved.disconnect(self.__getPolyline)
            self.PlotItem.scene().sigMouseClicked.disconnect(self.__offPolyline)
            # Update self.xwidth
            self.xwidth = new_xwidth
            # Clean up plot and populate it again (through __setupItems)
            for key in self.CurveItems:
                self.PlotItem.removeItem(self.CurveItems[key])
            self.PlotItem.removeItem(self.invisible_polyline)
            self.PlotItem.removeItem(self.ScatterItem)
            self.CurveItems = {}
            self.__setupItems()
            # Reconnect signals
            self.PlotItem.scene().sigMouseMoved.connect(self.__getPolyline)
            self.PlotItem.scene().sigMouseClicked.connect(self.__offPolyline)

    def __setupItems(self):
        """ This method creates a dict of curveitems from the polylines and
        plots them and the points at the vertices of the polyline.
        """
        # Create a dict with key=int corresponding to the self.plls index
        # and value = PlotCurveItem_ith
        self.CurveItems = {}
        for i in range(len(self.plls)):
            CurveItem = pg.PlotCurveItem(
            pen=pg.mkPen(color=self.lclr, width=self.lwdth))
            CurveItem.setClickable(False, width=7)
            #### CurveItem.setSkipFiniteCheck(True)   ## Needed recent version of pyqtgraph
            try:
                CurveItem.setData(self.plls[i][:, 0], self.plls[i][:, 1])
                self.PlotItem.addItem(CurveItem)
                self.CurveItems[i] = CurveItem
            except IndexError:
                continue  # This happens when messing up with offset
            
        # This invisible_polyline avoids to keep looping
        # on all the polylines when the mouse pointer is far from them
        polylines_linked = self.plls[0]
        for pll in self.plls[1:]:
            try:
                polylines_linked = np.vstack((polylines_linked, pll))
            except ValueError:
                continue  # This happens when trying to offset a "closed" concave polyline
        self.invisible_polyline = pg.PlotCurveItem(
            pen=pg.mkPen((255, 255, 0, 0), width=1))
        self.invisible_polyline.setClickable(False, width=100)
        self.invisible_polyline.setData(polylines_linked[:, 0], polylines_linked[:, 1])
        self.PlotItem.addItem(self.invisible_polyline)
        # Plot points at the vertices of the polylines
        self.ScatterItem = pg.ScatterPlotItem(pxMode=True, size=self.psz, brush= pg.mkBrush(self.pclr))
        self.ScatterItem.addPoints(polylines_linked[:, 0], polylines_linked[:, 1])
        # self.ScatterItem.setSymbol('crosshair')
        self.PlotItem.addItem(self.ScatterItem)
        
        # Create temp offset polyline plot item
        light_lclr = list(self.lclr)
        light_lclr[3] = 75
        light_lclr = tuple(light_lclr)
        self.tempOff = pg.PlotCurveItem(
        pen=pg.mkPen(color=light_lclr, width=self.lwdth))
        self.PlotItem.addItem(self.tempOff)

    def setSide(self):
        if self.offset > 0:
            self.side = 'right'
        elif self.offset < 0:
            self.side = 'left'

    def start(self):
        """ This method starts everything just as the other classes above.
        Call it after an instance of this class has been created.
        """
        if self.verbose:
            print("\nInitial number of polylines: ", len(self.plls))
            print(self.plls)
        # Initialize plots and data and connect signals
        self.__setupItems()
        self.PlotItem.scene().sigMouseMoved.connect(self.__getPolyline)
        self.PlotItem.sigRangeChanged.connect(self.__refresh_clickable_area)
        self.PlotItem.scene().sigMouseClicked.connect(self.__offPolyline)
        # Get initial viewrange of the ViewBox, needed only for
        # __refresh_clickable_area method
        vbstate = self.PlotItem.vb.getState(copy=True)
        viewrange = vbstate['viewRange']
        self.xwidth = viewrange[0][1] - viewrange[0][0]

        
    def stop(self):
        """ If called, this method disconnects all the signals """
        self.PlotItem.scene().sigMouseMoved.disconnect(self.__getPolyline)
        self.PlotItem.sigRangeChanged.disconnect(self.__refresh_clickable_area)
        self.PlotItem.scene().sigMouseClicked.disconnect(self.__offPolyline)


