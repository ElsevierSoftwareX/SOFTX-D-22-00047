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





###############################################################################
# This module contains all the functions that, given a point cloud, allow to
# obtain a set of MultiPolygons at specified z coordinates.
###############################################################################
import numpy as np
import shapely
import shapely.geometry as sg
import ezdxf
from ezdxf.addons.geo import GeoProxy





def make_zcoords(a, b, c, d):
    """
    a: zmin
    b: zmax
    c: n° of slices or slices' spacing, depending on param d
    d: 1=fixed number of slices, 2=fixed step height, 3=custom spacing
    
    Given zmin, zmax, param c and the spacing rule, returns a
    1-d numpy array of z coordinates
    """
    if d == 1:
        zcoords = np.linspace(float(a), float(b), int(c))
    elif d == 2:
        zcoords = np.arange(float(a), float(b), float(c))
    elif d == 3:
        pass 
    return zcoords





def make_slices(zcoords, pcl, thick, npts):
    """
    zcoords: 1-d np array of z coords as returned by func "make_zcoords()"
    pcl    : 3-columns xyz np array representing the whole point cloud
    thick  : thickness of the slice
    npts   : total number of points of the point cloud
    
    Given zcoords, pcl and the slice thickness, returns the dictionary
    "slices", defined as key=zcoord_i & value=slice_i, 
    where slice_i=np.array([[x1, y1, z1], [x2, y2, z2],..., [xn, yn, zn]]).
    
    npts and netpcl are needed only for 3D visualization purposes, as well as
    for the z coordinates in  slice_i
    """
    slices = {}  # Dictionary to be filled with key=zcoord_i, value=slice_i
    invmask = np.ones(npts, dtype=bool)  # For 3D visualization purposes
    
    for z in zcoords:
        mask = np.logical_and(pcl[:, 2] >= (z - thick/2), pcl[:, 2] <= (z + thick/2))
        slices[z] = pcl[mask, :]  # Fill the dict with key=z and value=slice_i
        invmask *= np.invert(mask)  # For 3D visualization purposes
    netpcl = pcl[invmask, :]  # Net point cloud for 3D visualization purposes
    return slices, netpcl





def find_centroids(minwthick, zcoords, slices, tolsl=10, tolpt=2, tol=0.01, checkpts=0.1, tolincr=1.35):
    """
    minwthick: Minimum wall thickness
    zcoords  : 1-d np array of z coords as that returned by func "make_zcoords()"
    slices   : Dictionary as that returned by function "make_slices()"
    
    tolsl    : Minimum number of pts that a slice must have to be considered, default=10
    tolpt    : Minimum number of points needed to calculate the centroid, default=2
    tol      : Radius of the circle which defines the area where to look for near points, default=0.01 if [m]
    checkpts : Fraction of the slice's points used to derive newtol, default=0.1
    tolincr  : Increment factor used to find the appropriate tolerance, default=1.35
    
    Given the arguments, returns the dictionary ctrds defined as key=zcoord_i &
    value=centroids_i, where centroids_i=np.array([[x1, y1, z1], [x2, y2, z2]....]).
    Z coordinates are stored in centroids_i only for 3D visualization purposes.
    """
    ctrds = {}  # Dict to be filled: key=zcoord_i, value=centroids derived from slice_i
    for z in zcoords:
        
        ##### CALIBRATION OF "tol" FOR EVERY SLICE #####
        # Extract a random subset from the whole slice -> slcheckpts
        slcheckpts = slices[z][np.random.choice(slices[z].shape[0], size=round(slices[z].shape[0] * checkpts), replace=False)]
        newtol = tol  # Only newtol will be used in the following. It could remain equal to tol or be increased
        while True:
            sumnearpts = 0
            for checkpt in slcheckpts:
                # For every point p in slcheckpts, count how many points are at most newtol away from it
                dists = np.sqrt(np.square(slices[z][:, 0] - checkpt[0]) + np.square(slices[z][:, 1] - checkpt[1]))
                nearpts = slices[z][dists <= newtol]
                sumnearpts += nearpts.shape[0]
            if newtol >= minwthick / tolincr:
                print('\nTolerance adopted for slice ', "%.3f" % z, ':', "%.5f" % newtol)
                break
            elif sumnearpts < (3.5 * tolpt * slcheckpts.shape[0]):  # Values smaller than 3tolpt don't work really well. Default = 3.5, grezzo = 15
                newtol *= tolincr
                continue
            else:
                print('\nTolerance adopted for slice ', "%.3f" % z, ':', "%.5f" % newtol)
                break

        ##### PROCEDURE FOR THE FIRST CENTROID #####
        empsl = slices[z][:, [0, 1]]        # Slice (2 columns np array) to be emptied
        if empsl.shape[0] < tolsl:
            ctrds[z] = None
            print("Slice:   ", "%.3f" % z, "            is empty")
            continue
        try:
            while True:
                stpnt = empsl[0]                    # Starting point
                empsl = np.delete(empsl, 0, 0)      # Removes the starting point from empsl
                dists = np.sqrt(np.square(empsl[:, 0] - stpnt[0]) + np.square(empsl[:, 1] - stpnt[1]))
                nearpts = empsl[dists <= newtol]
                if nearpts.shape[0] < tolpt:
                    continue
                ctrds[z] = np.array([[nearpts[:, 0].mean(), nearpts[:, 1].mean(), z]])
                empsl = empsl[dists > newtol]         # Removes the used points from empsl
                ncs = 1                               # Number of found centroids
                break
        except IndexError:
            print("Slice:   ", "%.3f" % z, "        Slice n of points:  ", slices[z].shape[0], "     discarded because n of points to generate the centroids is not sufficient")
            ctrds[z] = None
            continue
        
        ##### PROCEDURE FOR THE FOLLOWING CENTROIDS #####
        while True:
            nearestidx = np.argmin(np.sqrt(np.square(empsl[:, 0] - ctrds[z][ncs-1, 0]) + np.square(empsl[:, 1] - ctrds[z][ncs-1, 1])))
            nearest = empsl[nearestidx]              # The new starting point (nearest to the last found centroid)
            empsl = np.delete(empsl, nearestidx, 0)  # Removes the nearest point (new starting point) from empsl
            dists = np.sqrt(np.square(empsl[:, 0] - nearest[0]) + np.square(empsl[:, 1] - nearest[1]))
            nearpts = empsl[dists <= newtol]
            if nearpts.shape[0] < tolpt and empsl.shape[0] > 0:
                continue
            elif empsl.shape[0] < 1:
                break
            ctrds[z] = np.vstack((ctrds[z], np.array([nearpts[:, 0].mean(), nearpts[:, 1].mean(), z])))
            empsl = empsl[dists > newtol]
            ncs += 1
            if empsl.shape[0] < 1:
                break
        print('Slice:   ', "%.3f" % z, '        Slice n of points:  ', slices[z].shape[0], "     Derived centroids:  ", ctrds[z].shape[0])
    return ctrds





def make_polylines(minwthick, zcoords, ctrds, prcnt=1, minctrd=2, simpl_tol=0.025):
    """
    minwthick: Minimum wall thickness
    zcoords  : 1-d np array of z coords as that returned by func "make_zcoords()"
    ctrds    : Dict of centroyds as that returned by func "find_centroids()"
    prcnt    : Percentile used to derive a threshold to discard short polylines, default=5
    minctrd  : Min number of centroids that a polyline must possess not to be discarded, default=2
    simpl_tol: Tolerance used to simplify the polylines through Douglas-Peucker, default=0.02 if [m]
    
    Given the arguments, returns a dict "polys" defined as key=zcoord_i,
    value=[poly1, poly2,..., polyn], where polyn=np.array([[x1, y1], [x2, y2], ...).
    Similarly, the other returned dict cleanpolys contains simplified polylines.                                                          
    """
    polys = {} # Dict to be filled: key=zcoord_i, value=polylines
    for z in zcoords:
        # For each centroid, calculate the distance between it and the 
        # previous. If the distance is > than minwthick, then split the
        # unique polyline removing the segment between them.
        try:
            dists = np.sqrt(np.square(ctrds[z][1:, 0] - ctrds[z][0:-1, 0])+
                            np.square(ctrds[z][1:, 1] - ctrds[z][0:-1, 1]))
            tails = np.where((dists >= minwthick) == True)
            polys[z] = np.split(ctrds[z][:, : 2], tails[0] + 1)
        except TypeError:
            continue

    # Checks the polylines lengths and derives a threshold to discard the
    # ones made by few centroids
    polyslen = []
    for z in zcoords:
        try:
            for polyline in polys[z]:
                polyslen += [len(polyline)]
        except KeyError:
            continue
    polyslen = np.array(polyslen)
    tolpolyslen = round(np.nanpercentile(polyslen, prcnt))
    print('tol polylines length: ', tolpolyslen)

    cleanpolys = {}  # Dict to be filled: key=zcoord_i, value=clean polylines
    for z in zcoords:
        zcleanpolys = []
        try:
            for poly in polys[z]:
                if len(poly) < minctrd or len(poly) < tolpolyslen / 1.3: # 1.3 could be removed
                    continue
                rawpoly = sg.LineString(poly)
                cleanpoly = rawpoly.simplify(simpl_tol, preserve_topology=True)
                zcleanpolys += [np.array(cleanpoly)]
            cleanpolys[z] = zcleanpolys
            print(len(cleanpolys[z]), ' clean polylines found in slice ', "%.3f" % z)
        except KeyError:
            print('Slice ', z, ' skipped, it could be empty')
            continue
    return polys, cleanpolys





def make_polygons(minwthick, zcoords, cleanpolys, tolsimpl=0.035):
    """
    minwthick : Minimum wall thickness
    zcoords   : 1-d np array of z coords as that returned by func "make_zcoords()"
    cleanpolys: Dict of clean polylines as that returned by func "make_polylines()"
    tolsimpl  : Douglas-Peucker tol, used only if a polygon is invalid, default = 0.035
    
    Given the arguments, returns a dict "polygs" defined as key=zcoord_i
    and value=MultiPolygon, a common 2D geometry data structure used by
    the Shapely package.
    The returned list invalidpolygons is only needed to help the user solve problems in the gui.
    """
    # Remove empty zcoords due to manual removal of points/centroids/polylines
    z_to_remove = []
    for z in zcoords:
        try:
            for polyline in cleanpolys[z]:
                pass
        except KeyError:
            z_to_remove.append(z)
            print('removed: ', z)

    for r in z_to_remove:
        zcoords = zcoords[zcoords != r]
    
    # Make Polygons 
    invalidpolygons = []  # List of invalid polygons to be filled [zcoord1, zcoord2,..]
    polygs = {}  # Dict to be filled: key=zcoord_i, value=MultiPolygon
    
    for z in zcoords:
        pgons = []  # List of Polygons of slice z, to be filled
        for polyline in cleanpolys[z]:
            try:
                isvalid = 1
                newpgon = sg.Polygon(polyline)  # Just converted a polyline into the shapely Polygon data structure
            except ValueError:
                print('Error in slice ', z, 'Try to eliminate isolated segments')
            while True:
                if newpgon.is_valid:
                    break
#########################################################################################
### This portion of code tries to adjust an invalid polygon ############################
                elif tolsimpl >= minwthick / 2.5 and not newpgon.is_valid:
                    isvalid = 0
                    invalidpolygons += [z]  # Needed to show a warning message
                    # Generates a translated copy and performs an invalid operation to generate an useful error message
                    tranpgon = shapely.affinity.translate(newpgon, xoff=0.005, yoff=-0.005)
                    try:
                        invalidoperation = newpgon.symmetric_difference(tranpgon)
                    except Exception as e:
                        print('!!! Invalid polygon found in slice ' + "%.3f" % z + ' !!!')
                        print(e)
                    break
                else:
                    tolsimpl += minwthick / 50
                    newpgon.simplify(tolsimpl, preserve_topology=True)
#########################################################################################
            if isvalid == 0:
                continue
            else:
                pgons += [newpgon]
        print('slice: ', "%.3f" % z, ', independent polygons generated: ', len(pgons))

        try:
            # Perform boolean operation between Polygons to get a unique MultiPolygon per slice z
            temp = pgons[0]
            if len(pgons) >= 2:
                for j in range(len(pgons) - 1):
                    temp = temp.symmetric_difference(pgons[j + 1])
                polygs[z] = temp
            elif len(pgons) == 1:
                polygs[z] = temp
            else:
                print('Slice: ', "%.3f" % z, '   No poligons generated')
        except IndexError:
            print('Index error in "temp = pgons[0]"')
            pass
    return polygs, invalidpolygons





def export_dxf(zcoords, polygs, filepath):
    """
    This function saves a dxf file of hatches in the filepath.
    Once in AutoCAD, polylines can be retrieved using the command
    'hatchgenerateboundary'
    """
    dxfdoc = ezdxf.new('R2013')
    msp = dxfdoc.modelspace()

    for z in zcoords:
        pygeoint = sg.mapping(polygs[z])    # Or use asShape instead of mapping
        dxfentities = GeoProxy.to_dxf_entities(GeoProxy.parse(pygeoint))
        for entity in dxfentities:
            entity.rgb = (0, 133, 147)
            entity.transparency = (0.15)
            msp.add_entity(entity.translate(0, 0, z))
            
    dxfdoc.saveas(filepath)


