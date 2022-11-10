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





import numpy as np
import vispy.app
import vispy.scene
from vispy.scene import visuals




class Visp3dplot():
    """ Class that handles all the 3DViewer graphics.
    The view is defined into the __init__ method, while
    other ad-hoc methods are used to add items to it.
    """
    def __init__(self, resolution):
        self.resolution = resolution
        self.canvas = vispy.scene.SceneCanvas(title='3D Viewer', keys='interactive', show=True, bgcolor='white')
        self.view3d = self.canvas.central_widget.add_view()

    def print_cloud(self, plotdata, alpha):
        """ :param plotdata: 3-columns np array (mct.pcl or mct.netpcl)
        """
        self.scatter = visuals.Markers()
        if self.resolution == 1:
            self.pcl3dplotdata = plotdata
        else:
            self.npts_sub = int(round(self.resolution * plotdata.shape[0]))
            self.randpts = np.random.choice(plotdata.shape[0], size=self.npts_sub, replace=False)
            self.pcl3dplotdata = plotdata[self.randpts]
        self.scatter.set_data(self.pcl3dplotdata, symbol='disc',
                              face_color=(255 / 255, 255 / 255, 255 / 255, alpha), size=1.0)   ################### default size = 2.7
        self.view3d.add(self.scatter)

    def print_slices(self, mct):
        try:
            self.slices = visuals.Markers()
            self.sliceplot = mct.slices[mct.zcoords[0]]
            for i in mct.zcoords[1:]:
                self.sliceplot = np.vstack((self.sliceplot, mct.slices[i]))
            self.slices.set_data(self.sliceplot, symbol='disc',
                                 face_color=(0 / 255, 0 / 255, 255 / 255, 1), size=4.3)
            self.view3d.add(self.slices)
        except TypeError:
            print("Error in Visp3dplot.print_slices(): generate the slices first")

    def print_centr(self, mct):
        self.centroids = visuals.Markers()
        self.centrplot = mct.ctrds[mct.zcoords[0]]
        for i in mct.zcoords[1:]:
            self.centrplot = np.vstack((self.centrplot, mct.ctrds[i]))
        self.centroids.set_data(self.centrplot, symbol='disc',
                             face_color=(255 / 255, 0 / 255, 0 / 255, 1), size=7)
        self.view3d.add(self.centroids)

    def print_polylines(self, mct):
        xyzplines = []
        for z in mct.zcoords:
            for poly in mct.cleanpolys[z]:
                zcolumn = np.zeros((poly.shape[0], 1)) + z
                xyzplines += [np.hstack((poly, zcolumn))]

        plotitems = []
        for i in range(len(xyzplines)):
            plotitems += [visuals.Line()]
            plotitems[i].set_data(xyzplines[i], color=(0.05, 0.05, 1, 1), width=1)
            self.view3d.add(plotitems[i])

        vertices = xyzplines[0]
        for poly in xyzplines[1:]:
            vertices = np.vstack((vertices, poly))
        self.vertices = visuals.Markers()
        self.vertices.set_data(vertices, symbol='square',
                                face_color=(220 / 255, 30 / 255, 30 / 255, 1), size=2.7)
        self.view3d.add(self.vertices)

    def final3dsetup(self):
        self.view3d.camera = 'turntable'  # 'turntable'  # or 'arcball'
        axis = visuals.XYZAxis(parent=self.view3d.scene)

