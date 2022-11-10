____________________________________________________________________________________________________________
# Cloud2FEM
A finite element mesh generator based on point clouds of existing/historical structures

____________________________________________________________________________________________________________
### PREREQUISITES

Python 3 installed on your machine.
Use the Python package manager pip to install the following packages:
- PyQt5: pip install PyQt5
- PyQtGraph: pip install pyqtgraph
- VisPy: pip install vispy
- NumPy: pip install numpy
- pyntcloud: pip install pyntcloud
- Shapely: pip install Shapely
- ezdxf: pip install ezdxf

____________________________________________________________________________________________________________
### USAGE

#### Essential steps needed to obtain a FE mesh from a point cloud

1.  Run the file main_Cloud2FEM.py to open the graphical user interface
2.  Go to File/Import/Point Cloud... to open a point cloud in the .pcd or .ply file format
3.  Choose the slicing rule on the right panel
4.  Specify the slicing parameters according to the Zmin and Zmax values, to the point cloud density
    and to the desired level of detail of the final output
5.  Click "Generate slices"
6.  Specify the "Minimum wall thickness" according to the thickness of the walls in the structure or,
    more in general, to the dimensions of smallest detail you want to be represented in the final output
7.  Click "Generate Centroids"
8.  Click "Generate Polylines"
9.  Click "Generate Polygons"
10. Specify "X Grid dim" and "Y Grid dim" according to the desired refined of the FE mesh in the XY plane
11. Click "Generate Mesh"
12. Go to File/Export/Mesh... to store the generated FE mesh in the .inp file format

These steps generally allow to obtain a FE mesh if the input consists of a point cloud without 
criticalities and the software parameters are chosen appropriately.
An example is the point cloud utilized in the "Representative example" section of the article, 
for which the following parameters have been assumed:
- Slicing rule: Fixed step height
- From: 0.025
- to: 11.97
- step height: 0.2
- Minimum wall thickness: 0.3
- X Grid dim: 0.2
- Y Grid dim: 0.2


#### Actions needed to deal with criticalities

When action n° 9 is completed, a pop-up message communicates the outcome of the "Generate Polygons" step.
If one ore more slices are listed in the message, it means that these slices possess criticalities that need 
to be corrected before proceeding to step n° 11. These issues can be solved with the help of the editing
tools, which can be used to modify points of the slices, centroids or polylines. Common criticalities are
self-crossing polylines or the existence of isolated segments, which do not allow to generate valid polygons.
To locate the criticalities to be solved, the user can take advantage of the coordinates displayed in 
the error messages that appear in the terminal.

Once selected the faulty slice from the drop-down list in the left panel, the user can:
- After step n° 5, enter the Points edit mode by toggling "Points" and clicking "Edit" on the top bar.
  Using keyboard shortcuts (specified in the GUI) two remove approaches can be chosen.
- After step n° 7, enter the Centroids edit mode by toggling "Centroids" and clicking "Edit" on the top bar.
  Using keyboard shortcuts (specified in the GUI) two remove approaches can be chosen.
- After step n° 8, enter the Polylines edit mode by toggling "Polylines" and clicking "Edit" on the top bar.
  Using keyboard shortcuts (specified in the GUI) seven edit approaches can be chosen.

Once the editing on a slice has been completed, red markers on the right panel indicate the steps that
have to be performed again in order to be refreshed with the applied changes. As an example, if changes
are applied in the Centroids edit mode, steps n° 8, 9 and 11 must be executed before exporting the mesh.

