# coding=utf-8
# =============================================================================
# This AcquireAndDisplay.py shows how to get the image data, and then display images in a GUI.
# Currently, this program is limited to single camera use.
# NOTE: OpenCV2 must be installed on Python interpreter prior to running this example.

import PySpin
import sys
import cv2
import socket
import ImgProc
import time

global continue_recording
continue_recording = True

def acquire_and_display_images(cam, nodemap, nodemap_tldevice):
    """
    This function continuously acquires images from a device and display them in a GUI.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :param nodemap_tldevice: Transport layer device nodemap.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type nodemap_tldevice: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    global continue_recording

    sNodemap = cam.GetTLStreamNodeMap()

    # Change bufferhandling mode to NewestOnly
    node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
    if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
        print('Unable to set stream buffer handling mode.. Aborting...')
        return False

    # Retrieve entry node from enumeration node
    node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
    if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
        print('Unable to set stream buffer handling mode.. Aborting...')
        return False

    # Retrieve integer value from entry node
    node_newestonly_mode = node_newestonly.GetValue()

    # Set integer value from entry node as new value of enumeration node
    node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

    print('*** IMAGE ACQUISITION ***\n')
    try:
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False

        # Retrieve integer value from entry node
        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

        # Set integer value from entry node as new value of enumeration node
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        print('Acquisition mode set to continuous...')

        #  Begin acquiring images
        #
        #  *** NOTES ***
        #  What happens when the camera begins acquiring images depends on the
        #  acquisition mode. Single frame captures only a single image, multi
        #  frame catures a set number of images, and continuous captures a
        #  continuous stream of images.
        #
        #  *** LATER ***
        #  Image acquisition must be ended when no more images are needed.
        cam.BeginAcquisition()

        print('Acquiring images...')

        #  Retrieve device serial number for filename
        #
        #  *** NOTES ***
        #  The device serial number is retrieved in order to keep cameras from
        #  overwriting one another. Grabbing image IDs could also accomplish
        #  this.
        device_serial_number = ''
        node_device_serial_number = PySpin.CStringPtr(nodemap_tldevice.GetNode('DeviceSerialNumber'))
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
            device_serial_number = node_device_serial_number.GetValue()
            print('Device serial number retrieved as %s...' % device_serial_number)

        # Close program
        print('Press enter to close the program..')

        start_time = time.time()
        # Retrieve and display images
        while(continue_recording):
            try:

                #  Retrieve next received image
                #
                #  *** NOTES ***
                #  Capturing an image houses images on the camera buffer. Trying
                #  to capture an image that does not exist will hang the camera.
                #
                #  *** LATER ***
                #  Once an image from the buffer is saved and/or no longer
                #  needed, the image must be released in order to keep the
                #  buffer from filling up.
                
                image_result = cam.GetNextImage(1000)

                #  Ensure image completion
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())

                else:                    
                    # Getting the image data as a numpy array
                    image_data = image_result.GetNDArray()

                    global total_coords,ro
                    # Cropping the image to the ROI
                    crp_image = image_data[int(ro[1]):int(ro[1]+ro[3]), int(ro[0]):int(ro[0]+ro[2])]
                    
                    # Getting the Coordinates of the center of Pupil
                    (px,py, roi, rad) = ImgProc.detect_pupil(crp_image)
                    csv_str = str(px)+","+str(py)+",0,0"
                    
                    total_coords=total_coords+1 # Counting the number of coordinates

                    # Send the Coordinates over TCP/IP to Monkey Logic
                    global_connection.send(csv_str.encode())

                    # Displaying the pupil coordinates on the image
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(roi, str((px,py)), (0, 10), font, 0.4, (100, 255, 0), 2, cv2.LINE_AA)

                    # Draws an image on the current figure
                    cv2.imshow("Realtime",roi)
                
                    # Acquiring the key pressed by the user
                    key = cv2.waitKey(1) & 0xFF

                    # If user presses s, save the ROI coordinates
                    if key == ord('s'):
                        cv2.destroyAllWindows()
                        ro = cv2.selectROI (image_data) # Selecting the ROI
                        cv2.destroyAllWindows()

                        # Writing the ROI coordinates to a text file
                        with open('roi_coords.txt', 'wt') as f:
                            f.write('(top left x, top left y, width, height) = '+repr(ro)+'\n')
                            print("ROI file updated!")
                            f.close()

                    # If user presses r, reset the ROI coordinates
                    elif key == ord('r'):
                        cv2.destroyAllWindows()
                        ro = (0,0,540,720)  # Resetting the ROI
                        cv2.destroyAllWindows()

                        # Writing the ROI coordinates to a text file
                        with open('roi_coords.txt', 'wt') as f:
                            f.write('(top left x, top left y, width, height) = '+repr(ro)+'\n')
                            print("ROI file updated!")
                            f.close()

                    # If user presses q, close the program
                    elif key == ord('q'):
                        print('Program is closing...')
                        cv2.destroyAllWindows()
                        continue_recording=False                        

                #  Release image
                #
                #  *** NOTES ***
                #  Images retrieved directly from the camera (i.e. non-converted
                #  images) need to be released in order to keep from filling the
                #  buffer.
                image_result.Release()

            except PySpin.SpinnakerException as ex:
                print('Error: %s' % ex)
                return False
        
        end_time = time.time()
        global total_time
        total_time = (end_time-start_time)*(10**3)
        #  End acquisition
        #
        #  *** NOTES ***
        #  Ending acquisition appropriately helps ensure that devices clean up
        #  properly and do not need to be power-cycled to maintain integrity.
        cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return True


def run_single_camera(cam):
    """
    This function acts as the body of the example; please see NodeMapInfo example
    for more in-depth comments on setting up cameras.

    :param cam: Camera to run on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        nodemap_tldevice = cam.GetTLDeviceNodeMap()

        # Initialize camera
        cam.Init()

        # Retrieve GenICam nodemap
        nodemap = cam.GetNodeMap()

        # Acquire images
        result &= acquire_and_display_images(cam, nodemap, nodemap_tldevice)

        # Deinitialize camera
        cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def main():
    """
    Example entry point; notice the volume of data that the logging event handler
    prints out on debug despite the fact that very little really happens in this
    example. Because of this, it may be better to have the logger set to lower
    level in order to provide a more concise, focused log.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    result = True

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    # Get current library version
    version = system.GetLibraryVersion()
    print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()

    # Retrieve number of cameras
    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: %d' % num_cameras)

    # Finish if there are no cameras
    if num_cameras == 0:

        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

        print('Not enough cameras!')
        input('Done! Press Enter to exit...')
        return False
    
    # Fetch ROI Coordinates from roi_coords.txt
    print("Fetching ROI Coordinates...")
    global ro
    try:
        # If roi_coords.txt is present, then fetch ROI coordinates from it
        with open("roi_coords.txt", 'rt') as f:
            line = f.readline()   
            ro = eval(line[42:].strip())
            f.close()
            print("ROI Coordinates fetched successfully from roi_coords.txt")
    except:
        # If roi_coords.txt is not present, then set ROI coordinates to (0,0,540,720)
        print("Cannot Fetch ROI Coordinates from roi_coords.txt!")
        ro = (0,0,540,720)
        print("Setting ROI rectangle coordinates to ",ro)

    # Set up a TCP/IP server
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to server address and port 10001
    server_address = ('', 10001)
    tcp_socket.bind(server_address)

    # Listen on port 10001
    tcp_socket.listen(1)
    print("Waiting for connection: Kindly connect using Monkey Logic")
    connection, client = tcp_socket.accept()

    print("Connected to client IP: {}".format(client))

    # Receive and print data 32 bytes at a time
    data = connection.recv(32).decode('utf-8').strip()
    print("Received data: {}".format(data))
    
    
    global total_coords
    total_coords=0
    
    # If ok is received, then start the program
    if data=="ok":
        global global_connection    
        global_connection = connection            

        cam = cam_list[0]
        result &= run_single_camera(cam)

        # Release reference to camera
        # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
        # cleaned up when going out of scope.
        # The usage of del is preferred to assigning the variable to None.
        del cam

    # If not ok is received, then exit the program
    else:
        print("Error: Monkey Logic not connected properly")
        print("Kindly restart Monkey Logic and Connect Again")

    # Close socket
    connection.close()

    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()

    input('Done! Press Enter to exit...')

    # Print Net Time, Total Coordinates Sent, Framerate and Time to send one Coordinate
    global total_time
    print("\nNet time: {} ms".format(total_time))
    print("Total Coordinates Sent: ", total_coords)
    print("Framerate: {} Hz".format(1000*total_coords/total_time))
    if total_coords!=0:
        print("Time to send one Coordinate: {} ms".format(total_time/total_coords))
    return result


if __name__ == '__main__':
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
